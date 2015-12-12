# codding: utf-8
import os
from datetime import datetime
from sessions import connect, disconnect, ssh_connect, ssh_disconnect

VM_FOR_BACKUP = ['cent']
NFS_SR_PATH = '/var/run/sr-mount/'
ISCSI_SR_PATH = '/dev/VG_XenStorage-'
BACKUP_PATH = '/media/'
MOUNT_PATH = {'nfs': '10.10.10.61:/xenclusterbackup'}


def get_vm(session):
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


def get_vdi(session, vm):
	vbds = session.xenapi.VM.get_VBDs(vm)

	for vbd in vbds:
		vdi = session.xenapi.VBD.get_VDI(vbd)

		if 'NULL' in vdi:
			# FIXME: add to log
			print('VM', session.xenapi.VM.get_name_label(vm),
			      'had bad VDB, UUID: ', session.xenapi.VBD.get_uuid(vbd))
		else:
			sm_config = session.xenapi.VDI.get_sm_config(vdi)
			vdi_uuid = sm_config['vhd-parent']

			yield vdi, vdi_uuid


def get_sr(session, vdi):
	sr = session.xenapi.VDI.get_SR(vdi)
	sr_uuid = session.xenapi.SR.get_uuid(sr)
	sr_type = session.xenapi.SR.get_type(sr)

	return {'uuid': sr_uuid, 'type': sr_type}


def create_snapshot(session, vm, vm_name):
	try:
		snap = session.xenapi.VM.snapshot(vm, vm_name)
		print(snap)

		return snap
	except Exception as e:
		raise Exception('Creating snapshot error. Reason: ' + e)


def mount_folder(ssh_session):
	if "nfs" in MOUNT_PATH.keys():
		try:
			stdin, stdout, stderr = ssh_session.exec_command("mount -t nfs " +
			                                                 MOUNT_PATH[
				                                                 'nfs'] + ' ' +
			                                                 BACKUP_PATH)
			print(stdout.read(), stderr.read())
		except Exception as e:
			print(e, stdout.read(), stderr.read())


def copy_disk(sr, vdi, vdi_uuid, ssh_session, backup_dir, session):
	try:
		file_name = ('"' + session.xenapi.VDI.get_name_label(vdi) + '_' +
		             str(datetime.now().strftime("%Y-%m-%d")) + '.dd"')

		command = 'dd if={disk} of=' + backup_dir + '/' + file_name + \
		          ' bs=102400'

		if sr['type'] == 'lvmoiscsi':
			path = ISCSI_SR_PATH + sr['uuid']
			disk = path + '/VHD-' + vdi_uuid
			com = command.format(disk=disk)

			# Activate VHD for cloning
			ssh_session.exec_command('lvchange -ay ' + disk)

			stdin, stdout, stderr = ssh_session.exec_command(com)
			print(stdout.read(), stderr.read())

		elif sr['type'] == 'nfs':
			path = NFS_SR_PATH + sr['uuid']
			disk = path + '/' + vdi_uuid + '.vhd'
			com = command.format(disk=disk)

			stdin, stdout, stderr = ssh_session.exec_command(com)
			print(stdout.read(), stderr.read())

	except Exception as e:
		print('Copy disk error: ' + e)

	return file_name

def create_backup_dir(ssh_session, vm_name):
	dir_name = BACKUP_PATH + '/' + vm_name
	stdin, stdout, stderr = ssh_session.exec_command('mkdir ' + dir_name)
	error = stderr.read()

	if 'File exists' not in error:
		raise Exception('Failed to create backup dir: ' + error)

	return dir_name


def make_backup(session, vm_obj, vm_name):
	ssh_session = ssh_connect()
	mount_folder(ssh_session)

	try:
		backup_dir = create_backup_dir(ssh_session, vm_name)
	except Exception as e:
		print('make dir error ' + e)

	try:
		snapshot = create_snapshot(session, vm_obj, vm_name)
		vdi_uuids = get_vdi(session, snapshot)
		vdis = []

		for vdi, vdi_uuid in vdi_uuids:
			sr = get_sr(session, vdi)
			file_name = copy_disk(sr, vdi, vdi_uuid, ssh_session, backup_dir,
			                      session)
			vdis.append(file_name)
			session.xenapi.VDI.destroy(vdi)

		session.xenapi.VM.destroy(snapshot)
	except Exception as e:
		# FIXME: add to log
		print('exception', e)
		ssh_disconnect(ssh_session)

	ssh_disconnect(ssh_session)

	return vdis

# if __name__ == "__main__":
#
# 	session = connect('root', 'Go2Alex25O')
# 	ssh_session = ssh_connect()
# 	mount_folder(ssh_session)
#
# 	vms = get_vm(session)
#
# 	for vm_name in vms.keys():
#
# 		try:
# 			backup_dir = create_backup_dir(ssh_session, vm_name)
# 		except Exception as e:
# 			print(e)
# 			break
#
# 		try:
# 			snapshot = create_snapshot(session, vms[vm_name], vm_name)
# 			vdi_uuids = get_vdi(session, snapshot)
#
# 			for vdi, vdi_uuid in vdi_uuids:
# 				sr = get_sr(session, vdi)
# 				copy_disk(sr, vdi, vdi_uuid, ssh_session, backup_dir)
# 				session.xenapi.VDI.destroy(vdi)
#
# 			session.xenapi.VM.destroy(snapshot)
# 		except Exception as e:
# 			# FIXME: add to log
# 			print('exception', e)
#
# 	ssh_disconnect(ssh_session)
# 	disconnect(session)
