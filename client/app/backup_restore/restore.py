class Restore:
    NFS_SR_PATH = '/var/run/sr-mount/'
    ISCSI_SR_PATH = '/dev/VG_XenStorage-'
    BACKUP_PATH = '/media'
    MOUNT_PATH = {'nfs': '10.10.10.61:/xenclusterbackup'}

    def __init__(self, session, ssh_session):
        self.session = session
        self.ssh_session = ssh_session

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

    def restore_vdi(self, vm_obj, vdis, vm_name):
        print('restoring vdi', vdis)
        self.mount_folder()

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

        self.umount_folder()
