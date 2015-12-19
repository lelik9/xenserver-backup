from models import HostsModel, VmModel, BackupModel
import sys
from datetime import datetime

sys.path.append('../backup-restore/')
import backup, sessions


def _establish_session(host_id):
	host = HostsModel.get_host(host_id)

	sessions.HOST = host['host_ip']
	sessions.USER = host['login']
	sessions.PASSWORD = host['password']

	session = sessions.connect()
	ssh_session = sessions.ssh_connect()

	return session, ssh_session


class HostController:
	session = None

	def add_host(self, **kwargs):
		sessions.HOST = kwargs['host_ip']
		sessions.USER = kwargs['login']
		sessions.PASSWORD = kwargs['password']

		self.session = sessions.connect()
		host_id = HostsModel.add_managment_host(kwargs)
		vms = backup.get_vm(self.session)

		for vm in vms.keys():
			VmModel.add_vms(vm_name=vm, vm_object=vms[vm], host_id=host_id)

		sessions.disconnect(self.session)


class VmController:
	def backup_vm(self, vm_id):
		vm = VmModel.get_vm(vm_id)
		host_id = vm['host_id']
		session, ssh_session = _establish_session(host_id)

		print(vm)
		try:
			vdis = backup.make_backup(session=session,
			                          ssh_session=ssh_session,
			                          vm_obj=vm['vm_object'],
			                          vm_name=vm['vm_name'])
		except Exception as e:
			print(e)
			backup_result = {'result': 'fail'}
			return backup_result

		BackupModel.add_backup_info(vm_name=vm['vm_name'],
		                            vm_id=vm_id,
		                            vdis=vdis,
		                            date=datetime.now().strftime(
			                            "%Y-%m-%d_%H-%m"))

		sessions.disconnect(session)
		backup_result = {'result': 'ok'}
		return backup_result

	def remove_backup(self, backup_id, vm_id):
		vm = VmModel.get_vm(vm_id)
		host_id = vm['host_id']
		session, ssh_session = _establish_session(host_id)

		try:
			res = list(BackupModel.get_backup_info(backup_id))[0]

			BackupModel.remove_backup(backup_id)
			backup.mount_folder(ssh_session)

			for vdi in res['vdis']:
				stdin, stdout, stderr = ssh_session.exec_command(
					'rm -f /media/' +
					vdi)
		except:
			pass
		finally:
			sessions.ssh_disconnect(ssh_session)
			sessions.disconnect(session)
