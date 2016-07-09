from __future__ import print_function
from models import HostsModel, VmModel, BackupModel
import sys
from datetime import datetime

sys.path.append('../backup-restore/')
from app import app
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
    def __init__(self, user, password, ip):
        self.ip = ip

        try:
            self.session = sessions.connect(user, password, ip)
        except BaseException as e:
            # error = 'Host {} connection failed, cause: {}'.format(self.ip, str(e).encode('utf-8'))
            # app.LOGGER.error(error)
            raise BaseException('Host {} connection failed!'.format(self.ip))

        self.api = self.session.xenapi

    def add_host(self):
        hosts = []
        try:
            hosts_obj = self.api.host.get_all()
            pool_obj = self.api.pool.get_all()[0]
            pool_name = self.api.pool.get_name_label(pool_obj)

            is_pool_exist = HostsModel.get_pool(pool_name)
            print(is_pool_exist)
            if is_pool_exist is None:
                for host_obj in hosts_obj:
                    metrics = self.api.host.get_metrics(host_obj)
                    ip = self.api.host.get_address(host_obj)
                    host = {
                        'obj': host_obj,
                        'metrics': metrics,
                        'name': self.api.host.get_hostname(host_obj),
                        'ip': ip,
                        'mem_total': int(self.api.host_metrics.get_memory_total(metrics)),
                        'mem_free': int(self.api.host_metrics.get_memory_free(metrics)),
                        'live': self.api.host_metrics.get_live(metrics)
                        }
                    hosts.append(host)

                vms = self.get_host_vms()
                result = {
                    'pool': pool_name,
                    'hosts': hosts,
                    'vms': vms
                }
                HostsModel.add_host(result)
            else:
                raise BaseException('Pool already exist. For add new host in pool use REFRESH '
                                    'button')
        except BaseException as e:
            error = u'Add host {} failed, cause: {}'.format(self.ip, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

        sessions.disconnect(self.session)

    def get_host_vms(self):
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
