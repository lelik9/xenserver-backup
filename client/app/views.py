from flask import render_template, flash, redirect, request, url_for, send_file
from app import app
from forms import HostsForm, VmsForm, VmForm
from models import HostsModel, BackupStorageModel
from controller import HostController, VmController

from js_requests import *


@app.route('/login', methods=['GET'])
def login():
    pass


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')


@app.route('/storage', methods=['GET'])
def storage():
    if request.method == 'GET':
        try:
            BackupStorageModel.add_storage(sr_name=request.args.get('sr_name'),
                                           share=request.args.get('share'),
                                           user=request.args.get('user'),
                                           password=request.args.get('password'),
                                           protocol=request.args.get('protocol'))
        except Exception:
            pass
    return render_template('storage.html')


@app.route('/hosts/', methods=['GET'])
def hosts():
    if 'get' in request.args.keys():
        try:
            hosts = HostsModel.get_hosts()
            return response(result=hosts, resp_type='success')
        except BaseException as e:
            return response(result=str(e), resp_type='error')
    return render_template('hosts.html')


@app.route('/vms/<id>', methods=['POST', 'GET'])
def vms(id):
    # vms_form = VmsForm(id)

    return render_template('vms.html')


@app.route('/vm/<id>', methods=['POST', 'GET'])
def vm(id):
    vm_form = VmForm(id)
    vm_form.alert = False
    vm_controller = VmController()

    if vm_form.backup_btn.data:
        vm_form.backup_info = vm_controller.backup_vm(id)

    if request.method == 'GET':
        try:
            submit = request.args.get('submit')

            if submit is not None:
                backup_id = request.args.get('backup')

                if backup_id is not None:
                    if submit == 'remove':
                        vm_controller.remove_backup(backup_id, id)
                    elif submit == 'restore':
                        vm_controller.restore_vdi(backup_id, id)
                else:
                    vm_form.alert = True

                return redirect(url_for('vm', id=id))
        except Exception as e:
            print('exception: ', e)
        # vm_form.alert = True

    return render_template('vm.html', form=vm_form)
