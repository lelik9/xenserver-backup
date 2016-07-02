from models import HostsModel, VmModel, BackupModel
import sys
from datetime import datetime

sys.path.append('../backup-restore/')
from restore import Restore
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


class SrController:
    def scan_sr(self, host_id):
        session, ssh_session = _establish_session(host_id)

        sr_s = session.xenapi.SR.get_all()
        all_sr = filter(lambda x: (session.xenapi.SR.get_type(x) != 'udev') or
                                  (session.xenapi.SR.get_type(x) != 'iso'),
                        sr_s)

        for sr in all_sr:
            name = session.xenapi.SR.get_name_label(sr)
            type = session.xenapi.SR.get_type(sr)
            size = session.xenapi.SR.get_physical_size(sr)
            utilization = session.xenapi.SR.get_physical_utilisation(sr)


class VmController:

    @staticmethod
    def backup_vm(vm_id):
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
                    'rm -f /media/' + vm['vm_name'] + '/' +
                    vdi['name'])
                err = stderr.read()
                if err is not None:
                    print(err)
            backup.umount_folder(ssh_session)
        except:
            pass
        finally:
            sessions.ssh_disconnect(ssh_session)
            sessions.disconnect(session)

    def restore_vdi(self, backup_id, vm_id):
        vm = VmModel.get_vm(vm_id)
        host_id = vm['host_id']
        session, ssh_session = _establish_session(host_id)

        try:
            res = list(BackupModel.get_backup_info(backup_id))[0]
            restore = Restore(session, ssh_session)
            print('restore')
            restore.restore_vdi(vm['vm_object'], res['vdis'], vm['vm_name'])

        except Exception as e:
            print('restore fail ', e)
