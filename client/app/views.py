from flask import render_template, flash, redirect, request, url_for, send_file
from app import app
from forms import HostsForm, VmsForm, VmForm
from models import HostsModel
from controller import HostController, VmController


@app.route('/', methods=['POST', 'GET'])
def index():
	return render_template('index.html')


@app.route('/hosts', methods=['POST', 'GET'])
def hosts():
	host_form = HostsForm()
	host_form.hosts = HostsModel.get_managment_hosts()

	if host_form.add_host_btn.data:
		host_contorller = HostController()
		host_contorller.add_host(login=host_form.user_name.data,
		                         password=host_form.password.data,
		                         host_ip=host_form.host_ip_addr.data,
		                         host_name=host_form.host_name.data)

	return render_template('hosts.html', form=host_form)


@app.route('/vms/<id>', methods=['POST', 'GET'])
def vms(id):
	vms_form = VmsForm(id)

	return render_template('vms.html', form=vms_form)


@app.route('/vm/<id>', methods=['POST', 'GET'])
def vm(id):
	vm_form = VmForm(id)
	vm_controller = VmController()

	if vm_form.backup_btn.data:
		vm_form.backup_info = vm_controller.backup_vm(id)

	if request.method == 'POST':
		try:
			print(request.form['backup'])
		except Exception:
			# FIXME: send alert in page
			return render_template('vm.html', form=vm_form)

	return render_template('vm.html', form=vm_form)
