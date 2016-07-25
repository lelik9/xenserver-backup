# coding=utf-8
from app import app


class BaseBackup:
    BACKUP_PATH = '/media'
    NFS_SR_PATH = '/var/run/sr-mount/'
    ISCSI_SR_PATH = '/dev/VG_XenStorage-'
    ssh_session = None

    def _mount_folder(self, backup_sr):
        mount_path = backup_sr['share_path']

        if backup_sr['sr_type'] == "nfs":
            try:
                self.ssh_session.exec_command("mount -t nfs " + '"' + mount_path + '" ' +
                                              self.BACKUP_PATH)

                app.LOGGER.info('Mounted {} to {}'.format(mount_path, self.BACKUP_PATH))
            except Exception as e:
                error = 'Failed mount folder: {}; cause: {}'.format(mount_path, str(e))
                app.LOGGER.error(error)
                raise BaseException(error)

    def _umount_folder(self):
        try:
            self.ssh_session.exec_command("umount " + self.BACKUP_PATH)
            app.LOGGER.info('{} unmounted'.format(self.BACKUP_PATH))
        except Exception as e:
            app.LOGGER.error('Failed to unmount folder: {}; cause: {}'.format(self.BACKUP_PATH, e))