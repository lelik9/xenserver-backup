import paramiko
from XenAPI import Session

PORT = 22
USER = ''
PASSWORD = ''
HOST = ''


def ssh_connect():
    ssh_session = paramiko.SSHClient()
    ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_session.connect(hostname=HOST, username=USER, password=PASSWORD,
                        port=PORT)

    print('connected')
    return ssh_session


def ssh_disconnect(ssh_session):
    ssh_session.close()
    print('disconnected')


def connect(user, password, host):
    session = Session('http://' + host)
    session.login_with_password(user, password)
    print('connected')

    return session


def disconnect(session):
    session.logout()
    print('disconnected')
