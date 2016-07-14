# codding: utf-8
import os
import logging
from datetime import datetime

from sessions import *
from app import app
from app.models import HostsModel

NFS_SR_PATH = '/var/run/sr-mount/'
ISCSI_SR_PATH = '/dev/VG_XenStorage-'
BACKUP_PATH = '/media'


LOGGER = app.LOGGER


class VmBackup:
    """
        Class fo backup_restore VM
    """

    def __init__(self, vm_obj, backup_sr):
        self.session, self.ssh_session = self.__establish_session(vm_obj)
        self.backup_sr = backup_sr
        self.api = self.session.xenapi

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

        for vbd_s in vbds:
            try:
                vbd = {}
                vdi = self.api.VBD.get_VDI(vbd_s)
                vbd['device'] = self.api.VBD.get_device(vbd_s)
                vbd['bootable'] = self.api.VBD.get_bootable(vbd_s)
                vbd['mode'] = self.api.VBD.get_mode(vbd_s)
                vbd['type'] = self.api.VBD.get_type(vbd_s)
                vbd['unplag'] = self.api.VBD.get_unpluggable(vbd_s)
            except Exception as e:
                LOGGER.error('Get vdi of vbd {} failed; cause: {}'.format(vbd_s, e))

            if 'NULL' in vdi:
                # FIXME: add to log
                print('VM', self.api.VM.get_name_label(vm),
                      'had bad VDB, UUID: ', self.api.VBD.get_uuid(vbd_s))
            else:
                sm_config = self.api.VDI.get_sm_config(vdi)
                vdi_uuid = sm_config['vhd-parent']
                # print(vdi, vdi_uuid, vbd)
                yield vdi, vdi_uuid, vbd

    def __get_sr(self, vdi):
        sr = self.api.VDI.get_SR(vdi)
        sr_uuid = self.api.SR.get_uuid(sr)
        sr_type = self.api.SR.get_type(sr)

        return {'uuid': sr_uuid, 'type': sr_type}

    def __create_snapshot(self, vm, vm_name):
        try:
            snap = self.api.VM.snapshot(vm, vm_name)
            LOGGER.info('Created snapshot {}'.format(snap))

            return snap
        except Exception as e:
            raise Exception('Creating snapshot error. Reason: {}'.format(str(e)))

    def __mount_folder(self):
        if "nfs" in MOUNT_PATH.keys():
            try:
                stdin, stdout, stderr = self.ssh_session.exec_command("mount -t nfs " + '"' +
                                                                 MOUNT_PATH['nfs'] + '" ' +
                                                                 BACKUP_PATH)
                LOGGER.info('Mounted {} to {}'.format(MOUNT_PATH['nfs'], BACKUP_PATH))
            except Exception as e:
                LOGGER.error('Failed mount folder: {}; cause: {}, {}, {}'.format(
                    MOUNT_PATH['nfs'], e, stdout.read(), stderr.read()
                ))

    def __umount_folder(self):
        try:
            stdin, stdout, stderr = self.ssh_session.exec_command(
                "umount " + BACKUP_PATH)
        except Exception as e:
            print(e, stdout.read(), stderr.read())

    def __copy_disk(self, sr, vdi, vdi_uuid, ssh_session, backup_dir):
        try:
            file_name = ('"' + self.api.VDI.get_name_label(vdi) + '_' +
                         str(datetime.now().strftime("%Y-%m-%d_%H-%m")) + '.dd"')

            command = 'dd if={disk} of=' + backup_dir + '/' + file_name + ' bs=102400'

            if sr['type'] == 'lvmoiscsi':
                path = ISCSI_SR_PATH + sr['uuid']
                disk = path + '/VHD-' + vdi_uuid
                com = command.format(disk=disk)
                print('disk', disk)
                # Activate VHD for cloning
                ssh_session.exec_command('lvchange -ay ' + disk)
                print('command ', com)
                stdin, stdout, stderr = ssh_session.exec_command(com)
                print('out ', stdout.read(), ' err ', stderr.read())

            elif sr['type'] == 'nfs':
                path = NFS_SR_PATH + sr['uuid']
                disk = path + '/' + vdi_uuid + '.vhd'
                com = command.format(disk=disk)

                stdin, stdout, stderr = ssh_session.exec_command(com)
                print(stdout.read(), stderr.read())

        except Exception as e:
            print('Copy disk error: ' + e)

        return file_name

    def __create_backup_dir(self, dir_name):
        stdin, stdout, stderr = self.ssh_session.exec_command('mkdir -p ' + dir_name)
        error = stderr.read()

        if error is not None:
            raise Exception('Failed to create backup_restore dir: ' + error)

    def make_backup(self, ssh_session, vm_obj, vm_name):
        self.__mount_folder()

        try:
            backup_dir = BACKUP_PATH + '/' + vm_name
            self.__create_backup_dir(ssh_session, backup_dir)
        except Exception as e:
            LOGGER.error('Failed to create backup_restore dir: {}; cause: {}'.format(backup_dir, e))

        try:
            snapshot = self.__create_snapshot(vm_obj, vm_name)
            vdi_s = self.__get_vdi(snapshot)
            vdis = []

            for vdi, uuid, vbd in vdi_s:
                item = {}
                sr = self.__get_sr(vdi)
                file_name = self.__copy_disk(sr, vdi, uuid, ssh_session, backup_dir)

                item['name'] = file_name
                item['size'] = self.api.VDI.get_virtual_size(vdi)
                item['vbd'] = vbd

                vdis.append(item)
                self.api.VDI.destroy(vdi)

                self.api.VM.destroy(snapshot)
        except Exception as e:
            # FIXME: add to log
            LOGGER.critical(e)
            raise Exception('VDI backup_restore failed ' + e)

        self.__umount_folder()
        disconnect(self.session)
        ssh_disconnect(self.ssh_session)

        return vdis


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
