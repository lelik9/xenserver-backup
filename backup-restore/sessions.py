import paramiko
from XenAPI import Session

XEN_HOST = 'http://10.10.10.149'
PORT = 22
USER = 'root'
PASSWORD = 'Go2Alex25O'
HOST = '10.10.10.149'


def ssh_connect():
	ssh_session = paramiko.SSHClient()
	ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_session.connect(hostname=HOST, username=USER, password=PASSWORD,
	                    port=PORT)

	return ssh_session


def ssh_disconnect(ssh_session):
	ssh_session.close()


def connect(login, password, host):
	session = Session('http://' + host)
	session.login_with_password(login, password)
	print('connected')

	return session


def disconnect(session):
	session.logout()
	print('disconnected')