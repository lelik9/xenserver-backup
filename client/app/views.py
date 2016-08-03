from flask import render_template, redirect, url_for

from app import app
from models import HostsModel, BackupStorageModel, BackupModel
from controller import HostController, VmBackupController

from js_requests import *


@app.route('/login', methods=['GET'])
def login():
    pass


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')


@app.route('/storage/', methods=['GET'])
def storage():
    print(request.args)
    if 'get' in request.args.keys():
        try:
            sr = []
            if request.args['get'] == 'host_sr':
                hosts_model = HostsModel.get_instance()
                sr = hosts_model.get_sr()
            elif request.args['get'] == 'backup_sr':
                    sr = BackupStorageModel.get_backup_sr_wo_login()

            return response(result=sr, resp_type='success')
        except BaseException as e:
            return response(result=str(e), resp_type='error')

    return render_template('storage.html')


@app.route('/hosts/', methods=['GET'])
def hosts():
    if 'get' in request.args.keys():
        try:
            hosts_model = HostsModel.get_instance()
            hosts = hosts_model.get_hosts()
            return response(result=hosts, resp_type='success')
        except BaseException as e:
            return response(result=str(e), resp_type='error')
    return render_template('hosts.html')


@app.route('/vms/', methods=['GET'])
def vms():
    srs = BackupStorageModel.get_backup_sr_wo_login()

    if 'get' in request.args.keys():
        try:
            hosts_model = HostsModel.get_instance()
            vm = hosts_model.get_vm()
            return response(result=vm, resp_type='success')
        except BaseException as e:
            return response(result=str(e), resp_type='error')
    return render_template('vms.html', srs=srs)


@app.route('/backups/', methods=['GET'])
def backups():
    hosts_model = HostsModel.get_instance()
    hosts = hosts_model.get_hosts()

    if 'get' in request.args.keys():
        try:
            backups = BackupModel.get_backups()
            return response(result=backups, resp_type='success')
        except BaseException as e:
            return response(result=str(e), resp_type='error')

    return render_template('backups.html', hosts=hosts)

