# coding=utf-8
import paramiko
from XenAPI import Session

from app import app
from app.models import HostsModel

PORT = 22


def establish_session(obj, db_req):
    db_requests = {
        'get_pool_of_vm': HostsModel.get_pool_of_vm,
        'get_pool_of_host': HostsModel.get_pool_of_host
    }

    host_obj = db_requests[db_req](obj)

    host = host_obj['master']
    user = host_obj['login']
    password = host_obj['password']

    session = connect(user=user, password=password, host=host)
    ssh_session = ssh_connect(user=user, password=password, host=host)

    return session, ssh_session


def ssh_connect(user='', password='', host=''):
    try:
        ssh_session = paramiko.SSHClient()
        ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session.connect(hostname=host, username=user, password=password,
                            port=PORT)

        app.LOGGER.info('SSH connection to host {} done.'.format(host))
        return ssh_session
    except BaseException as e:
        error = 'SSH connection to host {} failed; cause: {}'.format(host, str(e))
        app.LOGGER.error(error)
        raise BaseException(error)


def ssh_disconnect(ssh_session):
    try:
        ssh_session.close()
        app.LOGGER.info('Disconnect ssh session {} done.'.format(ssh_session))
    except BaseException as e:
        error = 'Disconnect ssh session {} failed; cause: {}'.format(ssh_session, str(e))
        app.LOGGER.error(error)


def connect(user, password, host):
    try:
        session = Session('http://' + host)
        session.login_with_password(user, password)

        return session
    except BaseException as e:
        error = 'Establish xen session to host {} failed; cause: {}'.format(host, str(e))
        app.LOGGER.error(error)
        raise BaseException(error)


def disconnect(session):
    try:
        session.logout()
        app.LOGGER.info('Disconnect xen session done.')
    except BaseException as e:
        error = 'Disconnect xen session failed; cause: {}'.format(str(e))
        app.LOGGER.error(error)
