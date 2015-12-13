from models import HostsModel, VmModel, BackupModel
import sys
from datetime import datetime

sys.path.append('../backup-restore/')
import backup, sessions


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
	sessions = None
	ssh_session = None

	def backup_vm(self, vm_id):
		vm = VmModel.get_vm(vm_id)
		host_id = vm['host_id']
		host = HostsModel.get_host(host_id)

		sessions.HOST = host['host_ip']
		sessions.USER = host['login']
		sessions.PASSWORD = host['password']

		self.sessions = sessions.connect()

		self.ssh_session = sessions.ssh_connect()
		print(vm)
		try:
			vdis = backup.make_backup(session=self.sessions,
			                          ssh_session=self.ssh_session,
			                          vm_obj=vm['vm_object'],
			                          vm_name=vm['vm_name'])

			BackupModel.add_backup_info(vm_name=vm['vm_name'],
			                            vm_id=vm_id,
			                            vdis=vdis,
			                            date=datetime.now().strftime(
				                            "%Y-%m-%d_%H:%m"))

		except Exception as e:
			print(e)
			sessions.disconnect(self.sessions)
			backup_result = {'result': 'fail'}
			return backup_result

		sessions.disconnect(self.sessions)
		backup_result = {'result': 'ok'}
		return backup_result
