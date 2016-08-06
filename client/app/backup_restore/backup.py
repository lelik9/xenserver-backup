# coding=utf-8
import json
from datetime import datetime
import time

from sessions import *
from base_backup import BaseBackup
from app import app
from app.models import HostsModel, BackupModel


class VmBackup(BaseBackup):
    """
        Class fo backup_restore VM
    """

    def __init__(self, vm_obj, backup_sr):
        self.backup_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.vm_obj = vm_obj
        self.session, self.ssh_session = establish_session(vm_obj, 'get_pool_of_vm')
        self.backup_sr = backup_sr
        self.api = self.session.xenapi
        self.vm_name = self.api.VM.get_name_label(self.vm_obj)
        self.backup_dir = self.BACKUP_PATH + '/' + self.vm_name

        res = self._mount_folder(backup_sr)

    def __get_vdi(self, vm):
        vbds = self.api.VM.get_VBDs(vm)

        for vbd_obj in vbds:
            try:
                vdi_obj = self.api.VBD.get_VDI(vbd_obj)
                vbd_meta = {
                    'userdevice': self.api.VBD.get_userdevice(vbd_obj),
                    'bootable': self.api.VBD.get_bootable(vbd_obj),
                    'mode': self.api.VBD.get_mode(vbd_obj),
                    'type': self.api.VBD.get_type(vbd_obj),
                    'empty': self.api.VBD.get_empty(vbd_obj),
                    'unpluggable': self.api.VBD.get_unpluggable(vbd_obj),
                    'other_config': self.api.VBD.get_other_config(vbd_obj),
                    'qos_algorithm_type': self.api.VBD.get_qos_algorithm_type(vbd_obj),
                    'qos_algorithm_params': self.api.VBD.get_qos_algorithm_params(vbd_obj)
                }

                if 'NULL' in vdi_obj:
                    # FIXME: add to log
                    print('VM', self.api.VM.get_name_label(vm),
                          'had bad VBD, UUID: ', self.api.VBD.get_uuid(vbd_obj))
                else:
                    sm_config = self.api.VDI.get_sm_config(vdi_obj)
                    vdi_uuid = sm_config['vhd-parent']
                    yield vdi_obj, vdi_uuid, vbd_meta

            except Exception as e:
                app.LOGGER.error('Get vdi of vbd {} failed; cause: {}'.format(vbd_obj, e))

    def __get_sr(self, vdi):
        sr = self.api.VDI.get_SR(vdi)
        sr_uuid = self.api.SR.get_uuid(sr)
        sr_type = self.api.SR.get_type(sr)

        return {'uuid': sr_uuid, 'type': sr_type}

    def __create_snapshot(self):
        try:
            snap = self.api.VM.snapshot(self.vm_obj, self.vm_name)
            app.LOGGER.info('Created snapshot {}'.format(self.vm_name))

            return snap
        except Exception as e:
            raise Exception('Creating VM {} snapshot error; cause: {}'.format(self.vm_name, str(e)))

    def __copy_disk(self, sr, vdi, vdi_uuid):
        try:
            file_name = ('"' + self.api.VDI.get_name_label(vdi) + '_' +
                         self.backup_time + '.dd"')

            command = 'dd if={disk} of=' + self.backup_dir + '/' + file_name + ' bs=1M'
            com = ''
            if sr['type'] in ('lvmoiscsi', 'lvm'):
                path = self.ISCSI_SR_PATH + sr['uuid']
                disk = path + '/VHD-' + vdi_uuid
                com = command.format(disk=disk)
                print('disk', disk)
                # Activate VHD for cloning
                self.ssh_session.exec_command('lvchange -ay ' + disk)

            elif sr['type'] in ('nfs', 'ext'):
                path = self.NFS_SR_PATH + sr['uuid']
                disk = path + '/' + vdi_uuid + '.vhd'
                print('disk', disk)
                com = command.format(disk=disk)

            print('command ', com)

            stdin, stdout, stderr = self.ssh_session.exec_command(com)
            error = stderr.read()
            print(stdout.read(), error)

            if error != '' and 'records' not in error:
                err = 'Copy disk error: {}'.format(error)
                app.LOGGER.error(err)
                raise BaseException(err)

            return file_name

        except Exception as e:
            print('Copy disk error: {}' + str(e))

    def __create_backup_dir(self):
        # Hack for waiting complete mount
        time.sleep(1)

        stdin, stdout, stderr = self.ssh_session.exec_command('mkdir -p ' + self.backup_dir)
        error = stderr.read()

        if error != '':
            err = app.LOGGER.error('Failed to create backup dir: {}; cause: {}'.format(self.backup_dir,
                                                                                       error))
            raise Exception(err)

    def make_backup(self):
        self.__create_backup_dir()

        snapshot = self.__create_snapshot()

        try:
            vdi_objects = self.__get_vdi(snapshot)
            vdis_meta = []

            for vdi_obj, uuid, vbd in vdi_objects:
                sr = self.__get_sr(vdi_obj)
                print('sr', sr)
                file_name = self.__copy_disk(sr, vdi_obj, uuid)

                vdi_spec = self.__get_vdi_meta(vdi_obj=vdi_obj, vbd_meta=vbd, backup_file=file_name)

                vdis_meta.append(vdi_spec)
                self.api.VDI.destroy(vdi_obj)

            vm_meta, vifs_obj = self.__get_vm_meta()
            vifs_meta = self.__get_vifs_meta(vifs_obj)

            self.__make_meta_file(vdis_meta, vm_meta, vifs_meta)

        except Exception as e:
            error = 'VDI backup failed ' + str(e)
            app.LOGGER.critical(error)
            raise Exception(error)
        finally:
            self.api.VM.destroy(snapshot)
            self._umount_folder()
            disconnect(self.session)
            ssh_disconnect(self.ssh_session)

    def __make_meta_file(self, vdis_meta, vm_meta, vifs_meta):
        meta = json.dumps({
            'vm_name': self.vm_name,
            'vdis': vdis_meta,
            'vm': vm_meta,
            'vifs': vifs_meta
        })
        meta_file = self.vm_name+'_'+self.backup_time+'.meta'

        self.ssh_session.exec_command('echo '+meta+' >>'+self.backup_dir+'/'+meta_file)
        backup_model = BackupModel.get_instance()
        backup_model.add_backup_info({
            '_id': self.backup_time,
            'vm_name': self.vm_name,
            'vdis': vdis_meta,
            'vm': vm_meta,
            'vifs': vifs_meta,
            'meta_file': meta_file,
            'backup_sr': self.backup_sr['_id']
        })

    def __get_vdi_meta(self, vdi_obj, vbd_meta, backup_file):
        vdi_record = self.api.VDI.get_record(vdi_obj)

        vdi_meta = {
            'name_label': vdi_record['name_label'],
            'virtual_size': vdi_record['virtual_size'],
            'type': vdi_record['type'],
            'sharable': vdi_record['sharable'],
            'read_only': vdi_record['read_only'],
            'other_config': vdi_record['other_config'],
            'tags': vdi_record['tags'],
            'vbd_meta': vbd_meta,
            'backup_file': backup_file
        }
        return vdi_meta

    def __get_vm_meta(self):
        vm_record = self.api.VM.get_record(self.vm_obj)
        vifs_obj = vm_record['VIFs']
        vm_meta = {
            'memory_dynamic_min': vm_record['memory_dynamic_min'],
            'memory_dynamic_max': vm_record['memory_dynamic_max'],
            'memory_static_max': vm_record['memory_static_max'],
            'memory_static_min': vm_record['memory_static_min'],
            'actions_after_shutdown': vm_record['actions_after_shutdown'],
            'actions_after_crash': vm_record['actions_after_crash'],
            'actions_after_reboot': vm_record['actions_after_reboot'],
            'HVM_boot_policy': vm_record['HVM_boot_policy'],
            'HVM_boot_params': vm_record['HVM_boot_params'],
            'HVM_shadow_multiplier': vm_record['HVM_shadow_multiplier'],
            'VCPUs_at_startup': vm_record['VCPUs_at_startup'],
            'VCPUs_max': vm_record['VCPUs_max'],
            'other_config': vm_record['other_config']
        }
        return vm_meta, vifs_obj

    def __get_vifs_meta(self, vifs_obj):
        vifs = []

        for vif_obj in vifs_obj:
            vif_record = self.api.VIF.get_record(vif_obj)
            vif = {
                'device': vif_record['device'],
                'MTU': vif_record['MTU'],
                'MAC': vif_record['MAC'],
                'other_config': vif_record['other_config'],
                'qos_algorithm_type': vif_record['qos_algorithm_type'],
                'qos_algorithm_params': vif_record['qos_algorithm_params'],
                'name': self.api.network.get_record(vif_record['network'])['name_label']
            }
            vifs.append(vif)

        return vifs
