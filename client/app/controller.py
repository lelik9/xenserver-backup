from models import HostsModel, VmModel, BackupModel
import sys
from datetime import datetime

sys.path.append('../backup-restore/')
import backup, sessions


class HostController:
	session = None

	def add_host(self, **kwargs):
		self.session = sessions.connect(kwargs['login'], kwargs['password'],
		                                kwargs['host_ip'])
		host_id = HostsModel.add_managment_host(kwargs)
		vms = backup.get_vm(self.session)

		for vm in vms.keys():
			VmModel.add_vms(vm_name=vm, vm_object=vms[vm], host_id=host_id)

		sessions.disconnect(self.session)


class VmController:
	sessions = None

	def backup_vm(self, vm_id):
		vm = VmModel.get_vm(vm_id)
		host_id = vm['host_id']
		host = HostsModel.get_host(host_id)

		self.sessions = sessions.connect(host['login'], host['password'],
		                                 host['host_ip'])
		print(vm)
		try:
			vdis = backup.make_backup(session=self.sessions,
			                          vm_obj=vm['vm_object'],
			                          vm_name=vm['vm_name'])

			backup_info = {'vm_name': vm['vm_name'],
			               'vm_id': vm_id,
			               'vdis': vdis,
			               'date': datetime.now().strftime("%Y-%m-%d")}
			BackupModel.add_backup_info(backup_info)

		except Exception as e:
			print(e)
			sessions.disconnect(self.sessions)
			backup_info = {'result': 'fail'}
			return backup_info

		sessions.disconnect(self.sessions)
		backup_info.update({'result': 'ok'})
		return backup_info
