class Restore:
	NFS_SR_PATH = '/var/run/sr-mount/'
	ISCSI_SR_PATH = '/dev/VG_XenStorage-'
	BACKUP_PATH = '/media'
	MOUNT_PATH = {'nfs': '10.10.10.61:/xenclusterbackup'}

	def __init__(self, session, ssh_session):
		self.session = session
		self.ssh_session = session

	def mount_folder(self):
		if "nfs" in self.MOUNT_PATH.keys():
			try:
				stdin, stdout, stderr = \
					self.ssh_session.exec_command("mount -t nfs " +
					                              self.MOUNT_PATH['nfs'] + ' ' +
					                              self.BACKUP_PATH)

				print(stdout.read(), stderr.read())
			except Exception as e:
				print(e, stdout.read(), stderr.read())

	def umount_folder(self):
		try:
			stdin, stdout, stderr = \
				self.ssh_session.exec_command("umount " + self.BACKUP_PATH)

		except Exception as e:
			print(e, stdout.read(), stderr.read())

	def restore_vdi(self, vm_obj, *vdi):
		print('restoring vdi', vdi)
		# self.mount_folder()

		vm_state = self.session.xenapi.VM.get_power_state(vm_obj)

		if vm_state != 'halted':
			print('halted')

