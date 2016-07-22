# coding=utf-8
from sessions import *
from common import *

from app import app
from app.models import HostsModel, BackupModel


class Restore:
    NFS_SR_PATH = '/var/run/sr-mount/'
    ISCSI_SR_PATH = '/dev/VG_XenStorage-'

    def __init__(self, host_obj, vm_name, sr, vm_meta, vdis_meta, vifs_meta, backup_sr):
        self.session, self.ssh_session = establish_session(host_obj, 'get_pool_of_host')
        self.vm_name = vm_name
        self.sr = sr
        self.vm_meta = vm_meta
        self.vdis_meta = vdis_meta
        self.vifs_meta = vifs_meta
        self.backup_sr = backup_sr
        self.api = self.session.xenapi

    def restore_vm(self):
        mount_folder(self.ssh_session, self.backup_sr)

        vm_obj = self.__create_vm()

    def __create_vm(self):
        try:
            self.vm_meta['name_label'] = self.vm_name
            self.vm_meta['user_version'] = '1'
            self.vm_meta['is_a_template'] = False
            self.vm_meta['affinity'] = 'NULL'
            vm_obj = self.api.VM.create(self.vm_meta)
            print('vm object!', vm_obj)
            return vm_obj
        except BaseException as e:
            error = 'Failed create VM: {}; cause: {}'.format(self.vm_name, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    def restore_vdi(self, vm_obj, vdis, vm_name):
        print('restoring vdi', vdis)

        vm_state = self.session.xenapi.VM.get_power_state(vm_obj)
        print(vm_state)
        if vm_state == 'Halted':
            vbds = self.session.xenapi.VM.get_VBDs(vm_obj)
            # FIXME: SR stub
            sr_obj = self.session.xenapi.SR.get_by_name_label('iSCSI virtual '
                                                              'disk storage')[0]
            sr_uuid = self.session.xenapi.SR.get_uuid(sr_obj)
            print('vbds', vbds)
            if vbds is not None:
                # Removes all disk from VM
                for vbd in vbds:
                    vdi = self.session.xenapi.VBD.get_VDI(vbd)
                    if not 'NULL' in vdi:
                        sr_obj = self.session.xenapi.VDI.get_SR(vdi)
                        self.session.xenapi.VDI.forget(vdi)
                        self.session.xenapi.VDI.destroy(vdi)
                        self.session.xenapi.VBD.destroy(vbd)

            # Creating new VDI and restore data
            n = 0
            for vdi in vdis:
                vdi_spec = {
                    'name_label': vdi['name'],
                    'SR': sr_obj,
                    'virtual_size': vdi['size'],
                    'type': 'user',
                    'sharable': False,
                    'read_only': False,
                    'other_config': {}
                }
                try:
                    vdi_obj = self.session.xenapi.VDI.create(vdi_spec)
                except Exception as e:
                    # FIXME: logging!
                    print('vdi dont create: ' + str(e))
                    return

                # Create VBD for current VDI
                vbd_spec = {
                    'VM': vm_obj,
                    'VDI': vdi_obj,
                    'device': vdi['vbd']['device'],
                    'userdevice': str(n),
                    'bootable': vdi['vbd']['bootable'],
                    'mode': vdi['vbd']['mode'],
                    'type': vdi['vbd']['type'],
                    'empty': False,
                    'unpluggable': vdi['vbd']['unplag'],
                    'other_config': {},
                    'qos_algorithm_type': '',
                    'qos_algorithm_params': {}
                }
                try:
                    vbd_obj = self.session.xenapi.VBD.create(vbd_spec)
                    n += 1
                except Exception as e:
                    # FIXME: logging!
                    print('vbd dont create: ' + str(e))
                    return

                # Getting LV
                vdi_uuid = self.session.xenapi.VDI.get_uuid(vdi_obj)
                lvm = self.ISCSI_SR_PATH + sr_uuid + '/' + 'VHD-' + vdi_uuid

                # Activating LV
                stdin, stdout, stderr = self.ssh_session.exec_command(
                    "lvchange -ay " + lvm)

                error = stderr.read()

                if error != '':
                    print('LV activation failed ' + error)

                # Restoring data on disk
                command = "dd if=" + self.BACKUP_PATH + "/" + vm_name + "/" \
                          + vdi['name'] + " of=" + lvm + " bs=102400"
                print(command)
                stdin, stdout, stderr = self.ssh_session.exec_command(command)
                error = stderr.read()

                if error != '':
                    print('Restore vdi failed ' + error + stdout.read())


        else:
            self.session.xenapi.VM.clean_shutdown(vm_obj)
            self.restore_vdi(vm_obj, vdis)

        self.__umount_folder()
