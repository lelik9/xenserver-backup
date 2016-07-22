# coding=utf-8
from app import app

BACKUP_PATH = '/media'


def mount_folder(ssh_session, backup_sr):
    mount_path = backup_sr['share_path']

    if backup_sr['sr_type'] == "nfs":
        try:
            ssh_session.exec_command("mount -t nfs " + '"' + mount_path + '" ' +
                                     BACKUP_PATH)

            app.LOGGER.info('Mounted {} to {}'.format(mount_path, BACKUP_PATH))
        except Exception as e:
            error = 'Failed mount folder: {}; cause: {}'.format(mount_path, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)


def umount_folder(ssh_session):
    try:
        ssh_session.exec_command("umount " + BACKUP_PATH)
        app.LOGGER.info('{} unmounted'.format(BACKUP_PATH))
    except Exception as e:
        app.LOGGER.error('Failed to unmount folder: {}; cause: {}'.format(BACKUP_PATH, e))