# codding: utf-8
import os
import logging
from datetime import datetime
from sessions import disconnect, ssh_disconnect

NFS_SR_PATH = '/var/run/sr-mount/'
ISCSI_SR_PATH = '/dev/VG_XenStorage-'
BACKUP_PATH = '/media'
MOUNT_PATH = {'nfs': '10.10.10.61:/xenclusterbackup'}


def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("backup")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("test.log")

    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


LOGGER = create_logger()


def __get_vm(session):
    vm_list = {}
    all_vms = session.xenapi.VM.get_all()
    vms = filter(lambda x: (not session.xenapi.VM.get_is_a_template(x)) and
                           ('Control domain on host:' not in
                            session.xenapi.VM.get_name_label(x)),
                 all_vms)

    for vm in vms:
        vm_name = session.xenapi.VM.get_name_label(vm)
        vm_list[vm_name] = vm

    return vm_list


def __get_vdi(session, vm):
    vbds = session.xenapi.VM.get_VBDs(vm)

    for vbd_s in vbds:
        try:
            vbd = {}
            vdi = session.xenapi.VBD.get_VDI(vbd_s)
            vbd['device'] = session.xenapi.VBD.get_device(vbd_s)
            vbd['bootable'] = session.xenapi.VBD.get_bootable(vbd_s)
            vbd['mode'] = session.xenapi.VBD.get_mode(vbd_s)
            vbd['type'] = session.xenapi.VBD.get_type(vbd_s)
            vbd['unplag'] = session.xenapi.VBD.get_unpluggable(vbd_s)
        except Exception as e:
            LOGGER.error('Get vdi of vbd {} failed; cause: {}'.format(vbd_s, e))

        if 'NULL' in vdi:
            # FIXME: add to log
            print('VM', session.xenapi.VM.get_name_label(vm),
                  'had bad VDB, UUID: ', session.xenapi.VBD.get_uuid(vbd_s))
        else:
            sm_config = session.xenapi.VDI.get_sm_config(vdi)
            vdi_uuid = sm_config['vhd-parent']
            # print(vdi, vdi_uuid, vbd)
            yield vdi, vdi_uuid, vbd


def __get_sr(session, vdi):
    sr = session.xenapi.VDI.get_SR(vdi)
    sr_uuid = session.xenapi.SR.get_uuid(sr)
    sr_type = session.xenapi.SR.get_type(sr)

    return {'uuid': sr_uuid, 'type': sr_type}


def __create_snapshot(session, vm, vm_name):
    try:
        snap = session.xenapi.VM.snapshot(vm, vm_name)
        LOGGER.info('Created snapshot {}'.format(snap))

        return snap
    except Exception as e:
        raise Exception('Creating snapshot error. Reason: {}'.format(str(e)))


def __mount_folder(ssh_session):
    if "nfs" in MOUNT_PATH.keys():
        try:
            stdin, stdout, stderr = ssh_session.exec_command("mount -t nfs " +
                                                             MOUNT_PATH['nfs'] + ' ' +
                                                             BACKUP_PATH)
            LOGGER.info('Mounted {} to {}'.format(MOUNT_PATH['nfs'], BACKUP_PATH))
        except Exception as e:
            LOGGER.error('Failed mount folder: {}; cause: {}, {}, {}'.format(
                MOUNT_PATH['nfs'], e, stdout.read(), stderr.read()
            ))


def __umount_folder(ssh_session):
    try:
        stdin, stdout, stderr = ssh_session.exec_command(
            "umount " + BACKUP_PATH)
    except Exception as e:
        print(e, stdout.read(), stderr.read())


def __copy_disk(sr, vdi, vdi_uuid, ssh_session, backup_dir, session):
    try:
        file_name = ('"' + session.xenapi.VDI.get_name_label(vdi) + '_' +
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


def __create_backup_dir(ssh_session, dir_name):
    stdin, stdout, stderr = ssh_session.exec_command('mkdir -p ' + dir_name)
    error = stderr.read()

    if error is not None:
        raise Exception('Failed to create backup dir: ' + error)


def make_backup(session, ssh_session, vm_obj, vm_name):
    __mount_folder(ssh_session)

    try:
        backup_dir = BACKUP_PATH + '/' + vm_name
        __create_backup_dir(ssh_session, backup_dir)
    except Exception as e:
        LOGGER.error('Failed to create backup dir: {}; cause: {}'.format(backup_dir, e))

    try:
        snapshot = __create_snapshot(session, vm_obj, vm_name)
        vdi_s = __get_vdi(session, snapshot)
        vdis = []

        for vdi, uuid, vbd in vdi_s:
            item = {}
            sr = __get_sr(session, vdi)
            file_name = __copy_disk(sr, vdi, uuid, ssh_session, backup_dir, session)

            item['name'] = file_name
            item['size'] = session.xenapi.VDI.get_virtual_size(vdi)
            item['vbd'] = vbd

            vdis.append(item)
            session.xenapi.VDI.destroy(vdi)

        session.xenapi.VM.destroy(snapshot)
    except Exception as e:
        # FIXME: add to log
        LOGGER.critical(e)
        raise Exception('VDI backup failed ' + e)

    __umount_folder(ssh_session)
    disconnect(session)
    ssh_disconnect(ssh_session)

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
