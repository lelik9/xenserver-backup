# coding=utf-8
import paramiko
from XenAPI import Session

from app import app
from app.models import HostsModel


class Connection:
    """
        Class for creating ssh and Xen API connection to host
    """
    PORT = 22
    db_requests = {
        'get_pool_of_vm': HostsModel.get_pool_of_vm,
        'get_pool_of_host': HostsModel.get_pool_of_host
    }

    def __init__(self, obj, db_req='get_pool_of_vm'):
        host_obj = self.db_requests[db_req](obj)

        self.host = host_obj['master']
        self.user = host_obj['login']
        self.password = host_obj['password']

        self.__session = self.__connect()
        self.__ssh_session = self.__ssh_connect()

    def get_sessions(self):
        return self.__session, self.__ssh_session

    def disconnect(self):
        self.__disconnect()
        self.__ssh_disconnect()

    def __ssh_connect(self):
        try:
            ssh_session = paramiko.SSHClient()
            ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_session.connect(hostname=self.host, username=self.user, password=self.password,
                                port=self.PORT)

            app.LOGGER.info('SSH connection to host {} done.'.format(self.host))
            return ssh_session
        except BaseException as e:
            error = 'SSH connection to host {} failed; cause: {}'.format(self.host, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    def __ssh_disconnect(self):
        try:
            self.__ssh_session.close()
            app.LOGGER.info('Disconnect ssh session done.')
        except BaseException as e:
            error = 'Disconnect ssh session {} failed; cause: {}'.format(self.__ssh_session, str(e))
            app.LOGGER.error(error)

    def __connect(self):
        try:
            session = Session('http://' + self.host)
            session.login_with_password(self.user, self.password)

            return session
        except BaseException as e:
            error = 'Establish xen session to host {} failed; cause: {}'.format(self.host, str(e))
            app.LOGGER.error(error)
            raise BaseException(error)

    def __disconnect(self):
        try:
            self.__session.logout()
            app.LOGGER.info('Disconnect xen session done.')
        except BaseException as e:
            error = 'Disconnect xen session failed; cause: {}'.format(str(e))
            app.LOGGER.error(error)
