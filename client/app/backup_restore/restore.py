# coding=utf-8
from sessions import *
from base_backup import BaseBackup
from app import app
from app.models import HostsModel, BackupModel


class Restore(BaseBackup):
    def __init__(self, pool_name, vm_name, sr, backup_meta, backup_sr):
        super(Restore, self).__init__()
        self.session, self.ssh_session = establish_session(pool_name, 'get_pool_by_name')
        self.vm_name = vm_name
        self.sr = sr
        self.vm_meta = backup_meta['vm']
        self.vdis_meta = backup_meta['vdis']
        self.vifs_meta = backup_meta['vifs']
        self.old_vm_name = backup_meta['vm_name']
        self.backup_sr = backup_sr
        self.api = self.session.xenapi

    def run(self):
        pass

    def restore_vm(self):
        """
            Method for restoring VM
        """
        self._mount_folder(self.backup_sr)

        try:
            vm_obj = self.__create_vm()
            self.__create_vif(vm_obj=vm_obj)
            self.__create_vdi(vm_obj=vm_obj)
        except BaseException as e:
            error = 'VM restore failed. {}'.format(str(e))
            app.LOGGER.critical(error)
            raise Exception(error)
        finally:
            self._umount_folder()
            disconnect(self.session)
            ssh_disconnect(self.ssh_session)

    def __create_vm(self):
        try:
            vm_templ_obj = self.api.VM.get_by_name_label('Other install media')
            vm_templ_meta = self.api.VM.get_record(vm_templ_obj[0])

            for key in vm_templ_meta:
                if key in self.vm_meta.keys():
                    vm_templ_meta[key] = self.vm_meta[key]

            vm_templ_meta['name_label'] = self.vm_name
            vm_templ_meta['is_a_template'] = False

            vm_obj = self.api.VM.create(vm_templ_meta)
            return vm_obj
        except BaseException as e:
            error = 'Failed create VM: {}; cause: {}'.format(self.vm_name, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    def __create_vif(self, vm_obj):
        for vif in self.vifs_meta:
            vif['network'] = self.api.network.get_by_name_label(vif['name'])[0]
            vif.pop('name', None)
            vif['VM'] = vm_obj
            self.api.VIF.create(vif)

    def __create_vdi(self, vm_obj):
        for vdi in self.vdis_meta:
            vdi['SR'] = self.sr[0]
            vbd = vdi.pop('vbd_meta', None)

            vdi_obj = self.api.VDI.create(vdi)
            self.__create_vbd(vm_obj=vm_obj, vdi_obj=vdi_obj, vbd=vbd)
            self.__clone_backup_to_vdi(vdi_obj=vdi_obj, vdi_meta=vdi)

    def __create_vbd(self, vm_obj, vdi_obj, vbd):
        vbd['VM'] = vm_obj
        vbd['VDI'] = vdi_obj

        self.api.VBD.create(vbd)

    def __clone_backup_to_vdi(self, vdi_obj, vdi_meta):
        sr_type = self.api.SR.get_type(self.sr[0])
        sr_uuid = self.api.SR.get_uuid(self.sr[0])
        vdi_uuid = self.session.xenapi.VDI.get_uuid(vdi_obj)

        restore_command = "dd if=" + self.BACKUP_PATH + "/" + self.old_vm_name + "/" \
                          + vdi_meta['backup_file'] + " of={} bs=1M"

        if sr_type == 'lvmoiscsi':
            lvm = self.ISCSI_SR_PATH+sr_uuid+'/VHD-'+vdi_uuid
            # Activating LV
            stdin, stdout, stderr = self.ssh_session.exec_command(
                "lvchange -ay " + lvm)

            error = stderr.read()

            if error != '':
                err = 'LV activation failed: {}'.format(error)
                app.LOGGER.error(err)
                raise BaseException(err)

            restore_command = restore_command.format(lvm)
        elif sr_type in ('nfs', 'ext'):
            vhd_path = self.NFS_SR_PATH+sr_uuid+'/'+vdi_uuid+'.vhd'
            restore_command = restore_command.format(vhd_path)
        try:
            stdin, stdout, stderr = self.ssh_session.exec_command(restore_command)
            error = stderr.read()

            if error != '' and 'records' not in error:
                err = 'Restore vdi failed: {}'.format(error)
                app.LOGGER.error(err)
                raise BaseException(err)
        except BaseException as e:
            err = 'Restore vdi failed: {}'.format(str(e))
            app.LOGGER.error(err)
            raise BaseException(err)