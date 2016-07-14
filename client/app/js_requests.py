# coding=utf-8
import json
from flask import request
from pymongo import errors

from app import app
from controller import HostController, VmBackupController
from models import HostsModel, BackupStorageModel


def response(result=None, resp_type='success'):
    """

    :param result:
    :param resp_type:
    :return:
    """
    print(result)
    return json.dumps({u'result': result, 'type': resp_type})


@app.route('/host/', methods=['POST'])
def add_host():
    """

    :return:
    """
    ip = request.form['ip']
    login = request.form['login']
    password = request.form['password']

    try:
        host = HostController(login, password, ip)
        host.add_host()
    except BaseException as e:
        return response(result=str(e), resp_type='error')

    return response(result='Host added', resp_type='success')


@app.route('/host/', methods=['DELETE'])
def rm_host():
    """

    :return:
    """
    req = dict(request.form)
    result = 'Remove pool success'
    res_type = 'success'

    try:
        for host in req['check']:
            try:
                r = HostsModel.rm_pool(host)
                if r['ok'] == 0:
                    result = 'Remove pool failed'
                    res_type = 'error'
            except errors as e:
                result = 'Remove pool failed'
                res_type = 'error'
    except KeyError:
        result = 'Please select host'
        res_type = 'error'

    return response(result=result, resp_type=res_type)


@app.route('/vms/', methods=['POST'])
def scan_vm():
    ip = request.form['ip']
    login = request.form['login']
    password = request.form['password']

    try:
        host = HostController(login, password, ip)
        host.scan_vm()
    except BaseException as e:
        return response(result=str(e), resp_type='error')

    return response(result='Scanning VM completed', resp_type='success')


@app.route('/sr/', methods=['POST'])
def scan_sr():
    ip = request.form['ip']
    login = request.form['login']
    password = request.form['password']

    try:
        host = HostController(login, password, ip)
        host.scan_sr()
    except BaseException as e:
        return response(result=str(e), resp_type='error')

    return response(result='Scanning SR completed', resp_type='success')


@app.route('/backup_sr/', methods=['POST'])
def add_backup_sr():
    try:
        BackupStorageModel.add_storage({
            '_id': request.form['name'],
            'share_path': request.form['ip'],
            'sr_type': request.form['protocol'],
            'login': request.form['login'],
            'password': request.form['password'],
        })
        return response(result='Add backup_restore SR completed', resp_type='success')
    except errors.DuplicateKeyError:
        return response(result='SR with that name already exists', resp_type='error')
    except BaseException as e:
        return response(result='Add backup_restore sr failed. {}'.format(str(e)), resp_type='error')


@app.route('/backup_restore/', methods=['POST'])
def backup_vm():
    """

    :return:
    """
    req = dict(request.form)
    result = 'Backup success'
    res_type = 'success'

    try:
        for vm in req['vm[]']:
            VmBackupController.backup_vm(vm_obj=vm, backup_sr=req['sr'][0])
    except KeyError:
        result = 'Please select VM'
        res_type = 'error'
    except BaseException as e:
        result = str(e)
        res_type = 'error'
    return response(result=result, resp_type=res_type)