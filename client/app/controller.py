# coding=utf-8
from multiprocessing import Process
from pymongo import errors

from models import HostsModel, VmModel, BackupModel, BackupStorageModel

from app import app
from backup_restore.restore import Restore
from backup_restore import sessions
from backup_restore.backup import VmBackup


def proc(vm_obj, sr):
    vm_backup = VmBackup(vm_obj=vm_obj, backup_sr=sr)
    vm_backup.make_backup()


class HostController:
    def __init__(self, user, password, ip):
        self.ip = ip
        self.password = password
        self.user = user
        # self.connect = Co
        self.session = sessions.connect(user, password, ip)
        self.api = self.session.xenapi
        self.hosts_model = HostsModel.get_instance()

    def add_host(self):
        """
            Add hosts from target pool
        """
        hosts = []
        try:
            hosts_obj = self.api.host.get_all()
            pool_obj = self.api.pool.get_all()[0]
            pool_name = self.api.pool.get_name_label(pool_obj)

            is_pool_exist = self.hosts_model.get_pool(pool_name)

            if is_pool_exist is None:
                for host_obj in hosts_obj:
                    metrics = self.api.host.get_metrics(host_obj)
                    host = {
                        'obj': host_obj,
                        'metrics': metrics,
                        'name': self.api.host.get_hostname(host_obj),
                        'ip': self.api.host.get_address(host_obj),
                        'mem_total': int(self.api.host_metrics.get_memory_total(metrics)),
                        'mem_free': int(self.api.host_metrics.get_memory_free(metrics)),
                        'live': self.api.host_metrics.get_live(metrics)
                    }
                    hosts.append(host)

                result = {
                    'pool': pool_name,
                    'hosts': hosts,
                    'master': self.ip,
                    'login': self.user,
                    'password': self.password
                }
                self.hosts_model.add_host(result)
            else:
                raise BaseException('Pool already exist. For add new host in pool use REFRESH '
                                    'button')
        except BaseException as e:
            error = 'Add host {} failed, cause: {}'.format(self.ip, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

        sessions.disconnect(self.session)

    def scan_vm(self):
        """
            Scanning for VM's in existing pool
        """
        try:
            vm_list = []
            all_vms = self.api.VM.get_all()
            vms = filter(lambda x: (not self.api.VM.get_is_a_template(x)) and
                                   ('Control domain on host:' not in
                                    self.api.VM.get_name_label(x)),
                         all_vms)

            for vm in vms:
                metrics = self.api.VM.get_metrics(vm)

                vm_info = {
                    'obj': vm,
                    'name': self.api.VM.get_name_label(vm),
                    'metrics': metrics,
                    'memory': int(self.api.VM_metrics.get_memory_actual(metrics)),
                    'CPU': int(self.api.VM_metrics.get_VCPUs_number(metrics)),
                    'state': self.api.VM_metrics.get_state(metrics)
                }
                vm_list.append(vm_info)

            res = self.hosts_model.set_host_info(self.ip, 'vm', vm_list)
            if res['nModified'] == 0:
                error = u"Scan VM's failed. Unable to update DB"
                app.LOGGER.error(error)
                raise BaseException(error)
        except BaseException as e:
            error = u"Scan VM's failed, cause: {}".format(str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    def scan_sr(self):
        """
            Scanning for SR in current pool without 'iso' and 'udev' type.
        """
        try:
            sr_list = []
            all_sr = self.api.SR.get_all()

            for sr in all_sr:
                sr_type = self.api.SR.get_type(sr)
                if sr_type not in ('udev', 'iso'):
                    sr_info = {
                        'obj': sr,
                        'name': self.api.SR.get_name_label(sr),
                        'type': sr_type,
                        'size': int(self.api.SR.get_physical_size(sr)),
                        'utilization': int(self.api.SR.get_physical_utilisation(sr)),
                        'shared': self.api.SR.get_shared(sr)
                    }
                    sr_list.append(sr_info)

            res = self.hosts_model.set_host_info(self.ip, 'sr', sr_list)
            if res['nModified'] == 0:
                error = u"Scan SR failed. Unable to update DB"
                app.LOGGER.error(error)
                raise BaseException(error)
        except BaseException as e:
            error = u"Scan SR failed, cause: {}".format(str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    @staticmethod
    def rm_host(hosts=None):
        result = 'Remove pool success'
        res_type = 'success'

        if hosts is not None:
            for host in hosts:
                try:
                    hosts_model = HostsModel.get_instance()
                    r = hosts_model.rm_pool(host)
                    if r['ok'] == 0:
                        result = 'Remove pool failed'
                        res_type = 'error'
                except errors:
                    result = 'Remove pool failed'
                    res_type = 'error'
        else:
            result = 'No hosts selected'
            res_type = 'error'

        return result, res_type


class VmBackupController:
    @staticmethod
    def backup_vm(vm_obj, backup_sr):
        sr = BackupStorageModel.get_backup_sr(backup_sr)

        # proccess = Process(target=proc, args=(vm_obj, sr))
        t1 = threading.Thread(target=proc, args=(vm_obj, sr))
        try:
            t1.start()
            t1.join()
            # proccess.start()
            # proccess.join()

        except BaseException as e:
            error = u"VM backup failed, cause: {}".format(str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    @staticmethod
    def restore_backup(vm_name, host_obj, sr, backup_id):
        backup_meta = BackupModel.get_backup(backup_id)

        vm_meta = backup_meta['vm']
        vdis_meta = backup_meta['vdis']
        vifs_meta = backup_meta['vifs']
        backup_id = backup_meta['backup_sr']
        old_vm_name = backup_meta['vm_name']

        backup_sr = BackupStorageModel.get_backup_sr(backup_id)

        restore = Restore(host_obj, vm_name, sr, vm_meta, vdis_meta, vifs_meta, backup_sr,
                          old_vm_name)
        restore.restore_vm()


        # def remove_backup(self, backup_id, vm_id):
        #     vm = VmModel.get_vm(vm_id)
        #     host_id = vm['host_id']
        #     session, ssh_session = _establish_session(host_id)
        #
        #     try:
        #         res = list(BackupModel.get_backups(backup_id))[0]
        #
        #         BackupModel.remove_backup(backup_id)
        #         backup_restore._mount_folder(ssh_session)
        #
        #         for vdi in res['vdis']:
        #             stdin, stdout, stderr = ssh_session.exec_command(
        #                 'rm -f /media/' + vm['vm_name'] + '/' +
        #                 vdi['name'])
        #             err = stderr.read()
        #             if err is not None:
        #                 print(err)
        #         backup_restore._umount_folder(ssh_session)
        #     except:
        #         pass
        #     finally:
        #         sessions.ssh_disconnect(ssh_session)
        #         sessions.disconnect(session)


        # class SrController:
        #     def scan_sr(self, host_id):
        #         session, ssh_session = _establish_session(host_id)
        #
        #         sr_s = session.xenapi.SR.get_all()
        #         all_sr = filter(lambda x: (session.xenapi.SR.get_type(x) != 'udev') or
        #                                   (session.xenapi.SR.get_type(x) != 'iso'),
        #                         sr_s)
        #
        #         for sr in all_sr:
        #             name = session.xenapi.SR.get_name_label(sr)
        #             type = session.xenapi.SR.get_type(sr)
        #             size = session.xenapi.SR.get_physical_size(sr)
        #             utilization = session.xenapi.SR.get_physical_utilisation(sr)
