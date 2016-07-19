# coding=utf-8
import json
from datetime import datetime

from sessions import *
from app import app
from app.models import HostsModel

NFS_SR_PATH = '/var/run/sr-mount/'
ISCSI_SR_PATH = '/dev/VG_XenStorage-'
BACKUP_PATH = '/media'


class VmBackup:
    """
        Class fo backup_restore VM
    """

    def __init__(self, vm_obj, backup_sr):
        self.backup_time = str(datetime.now().strftime("%Y-%m-%d_%H-%m"))
        self.vm_obj = vm_obj
        self.session, self.ssh_session = self.__establish_session(vm_obj)
        self.backup_sr = backup_sr
        self.api = self.session.xenapi
        self.vm_name = self.api.VM.get_name_label(self.vm_obj)
        self.backup_dir = BACKUP_PATH + '/' + self.vm_name

    def __establish_session(self, vm_obj):
        host_obj = HostsModel.get_host_of_vm(vm_obj)
        host = host_obj['master']
        user = host_obj['login']
        password = host_obj['password']

        session = connect(user=user, password=password, host=host)
        ssh_session = ssh_connect(user=user, password=password, host=host)

        return session, ssh_session

    def __get_vm(self):
        vm_list = {}
        all_vms = self.api.VM.get_all()
        vms = filter(lambda x: (not self.api.VM.get_is_a_template(x)) and
                               ('Control domain on host:' not in
                                self.api.VM.get_name_label(x)),
                     all_vms)

        for vm in vms:
            vm_name = self.api.VM.get_name_label(vm)
            vm_list[vm_name] = vm

        return vm_list

    def __get_vdi(self, vm):
        vbds = self.api.VM.get_VBDs(vm)

        for vbd_obj in vbds:
            try:
                vdi_obj = self.api.VBD.get_VDI(vbd_obj)
                vbd_spec = {
                    'device': self.api.VBD.get_device(vbd_obj),
                    'userdevice': self.api.VBD.get_userdevice(vbd_obj),
                    'bootable': self.api.VBD.get_bootable(vbd_obj),
                    'mode': self.api.VBD.get_mode(vbd_obj),
                    'type': self.api.VBD.get_type(vbd_obj),
                    'empty': self.api.VBD.get_empty(vbd_obj),
                    'unpluggable': self.api.VBD.get_unpluggable(vbd_obj),
                    'other_config': self.api.VBD.get_other_config(vbd_obj),
                    'qos_algorithm_type': self.api.VBD.get_qos_algorithm_type(vbd_obj),
                    'qos_algorithm_params': self.api.VBD.get_qos_algorithm_params(vbd_obj)
                }

                if 'NULL' in vdi_obj:
                    # FIXME: add to log
                    print('VM', self.api.VM.get_name_label(vm),
                          'had bad VBD, UUID: ', self.api.VBD.get_uuid(vbd_obj))
                else:
                    sm_config = self.api.VDI.get_sm_config(vdi_obj)
                    vdi_uuid = sm_config['vhd-parent']
                    yield vdi_obj, vdi_uuid, vbd_spec

            except Exception as e:
                app.LOGGER.error('Get vdi of vbd {} failed; cause: {}'.format(vbd_obj, e))

    def __get_sr(self, vdi):
        sr = self.api.VDI.get_SR(vdi)
        sr_uuid = self.api.SR.get_uuid(sr)
        sr_type = self.api.SR.get_type(sr)

        return {'uuid': sr_uuid, 'type': sr_type}

    def __create_snapshot(self):
        try:
            snap = self.api.VM.snapshot(self.vm_obj, self.vm_name)
            app.LOGGER.info('Created snapshot {}'.format(self.vm_name))

            return snap
        except Exception as e:
            raise Exception('Creating VM {} snapshot error; cause: {}'.format(self.vm_name, str(e)))

    def __mount_folder(self, backup_sr):
        mount_path = backup_sr['share_path']

        if backup_sr['sr_type'] == "nfs":
            try:
                self.ssh_session.exec_command("mount -t nfs " + '"' + mount_path + '" ' +
                                              BACKUP_PATH)

                app.LOGGER.info('Mounted {} to {}'.format(mount_path, BACKUP_PATH))
            except Exception as e:
                error = 'Failed mount folder: {}; cause: {}'.format(mount_path, str(e))
                app.LOGGER.error(error)
                raise BaseException(error)

    def __umount_folder(self):
        try:
            self.ssh_session.exec_command("umount " + BACKUP_PATH)
            app.LOGGER.info('{} unmounted'.format(BACKUP_PATH))
        except Exception as e:
            app.LOGGER.error('Failed to unmount folder: {}; cause: {}'.format(BACKUP_PATH, e))

    def __copy_disk(self, sr, vdi, vdi_uuid):
        try:
            file_name = ('"' + self.api.VDI.get_name_label(vdi) + '_' +
                         self.backup_time + '.dd"')

            command = 'dd if={disk} of=' + self.backup_dir + '/' + file_name + ' bs=102400'

            if sr['type'] == 'lvmoiscsi':
                path = ISCSI_SR_PATH + sr['uuid']
                disk = path + '/VHD-' + vdi_uuid
                com = command.format(disk=disk)
                print('disk', disk)
                # Activate VHD for cloning
                self.ssh_session.exec_command('lvchange -ay ' + disk)
                print('command ', com)
                stdin, stdout, stderr = self.ssh_session.exec_command(com)
                print('out ', stdout.read(), ' err ', stderr.read())

            elif sr['type'] in ('nfs', 'ext'):
                path = NFS_SR_PATH + sr['uuid']
                disk = path + '/' + vdi_uuid + '.vhd'
                com = command.format(disk=disk)

                stdin, stdout, stderr = self.ssh_session.exec_command(com)
                print(stdout.read(), stderr.read())
            return file_name

        except Exception as e:
            print('Copy disk error: ' + e)

    def __create_backup_dir(self):
        stdin, stdout, stderr = self.ssh_session.exec_command('mkdir -p ' + self.backup_dir)
        error = stderr.read()

        if error != '':
            err = app.LOGGER.error('Failed to create backup dir: {}; cause: {}'.format(self.backup_dir,
                                                                                       error))
            raise Exception(err)

    def make_backup(self, backup_sr):
        self.__mount_folder(backup_sr)

        self.__create_backup_dir()

        snapshot = self.__create_snapshot()

        try:
            vdi_objects = self.__get_vdi(snapshot)
            vdi_list = []

            for vdi_obj, uuid, vbd in vdi_objects:
                sr = self.__get_sr(vdi_obj)
                file_name = self.__copy_disk(sr, vdi_obj, uuid)

                vdi_spec = self.create_vdi_spec(vdi_obj=vdi_obj, vbd_spec=vbd, backup_file=file_name)

                vdi_list.append(vdi_spec)
                self.api.VDI.destroy(vdi_obj)

            self.make_meta_file(vdi_list)
            self.api.VM.destroy(snapshot)

            self.__umount_folder()
            disconnect(self.session)
            ssh_disconnect(self.ssh_session)

        except Exception as e:
            error = 'VDI backup failed ' + str(e)
            app.LOGGER.critical(error)

            self.api.VM.destroy(snapshot)
            self.__umount_folder()
            disconnect(self.session)
            ssh_disconnect(self.ssh_session)

            raise Exception(error)

    def make_meta_file(self, meta):
        pass
        # json.dump(meta, open(self.backup_dir + '/' + self.vm_name + self.backup_time + '.meta',
        #                      'w'))

    def create_vdi_spec(self, vdi_obj, vbd_spec, backup_file):
        return {
            'name_label': self.api.VDI.get_name_label(vdi_obj),
            'virtual_size': self.api.VDI.get_virtual_size(vdi_obj),
            'type': self.api.VDI.get_type(vdi_obj),
            'sharable': self.api.VDI.get_sharable(vdi_obj),
            'read_only': self.api.VDI.get_read_only(vdi_obj),
            'other_config': self.api.VDI.get_other_config(vdi_obj),
            'tags': self.api.VDI.get_tags(vdi_obj),
            'managed': self.api.VDI.get_managed(vdi_obj),
            'missing': self.api.VDI.get_missing(vdi_obj),
            'vbd_spec': vbd_spec,
            'backup_file': backup_file
        }

    def vm_meta_backup(session):
        pass

# if __name__ == "__main__":
#

# 	session = connect('', '')

# 	session = connect('login', 'password', '10.10.10.149')
# 	ssh_session = ssh_connect()
# 	mount_folder(ssh_session)
#
# 	vms = get_vm(session)
#
# 	for vm_name in vms.keys():
# 		print(session, vms[vm_name], vm_name)
# 		make_backup(session, u'OpaqueRef:f7e12f0d-d80a-5f89-5028-2b084cc65ad5',
# 		            u'cent')
# 		# try:
# 		# 	backup_dir = create_backup_dir(ssh_session, vm_name)
# 		# except Exception as e:
# 		# 	print(e)
# 		# 	break
# 		#
# 		# try:
# 		# 	snapshot = create_snapshot(session, vms[vm_name], vm_name)
# 		# 	vdi_uuids = get_vdi(session, snapshot)
# 		#
# 		# 	for vdi, vdi_uuid in vdi_uuids:
# 		# 		sr = get_sr(session, vdi)
# 		# 		copy_disk(sr, vdi, vdi_uuid, ssh_session, backup_dir, session)
# 		# 		session.xenapi.VDI.destroy(vdi)
# 		#
# 		# 	session.xenapi.VM.destroy(snapshot)
# 		# except Exception as e:
# 		# 	# FIXME: add to log
# 		# 	print('exception', e)
#
# 	ssh_disconnect(ssh_session)
# 	disconnect(session)