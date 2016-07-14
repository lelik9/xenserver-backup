from flask_wtf import Form
from wtforms import StringField, SelectField, SubmitField, RadioField
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms.validators import DataRequired, length
from models import VmModel, BackupModel


class HostsForm(Form):
	host_name = StringField('host_name', validators=[DataRequired()])
	host_ip_addr = StringField('host_ip', validators=[DataRequired()])
	user_name = StringField('user_name', validators=[DataRequired()])
	password = PasswordField('passwor', validators=[DataRequired()])
	add_host_btn = SubmitField('add host')


class VmsForm(Form):
	all_vm = None

	def __init__(self, id):
		self.all_vm = VmModel.get_vms(host_id=id)

class VmForm(Form):
	vm = None
	backups = None
	backup_btn = SubmitField('backup_restore now')
	sel_backup = RadioField()

	def __init__(self, id):
		Form.__init__(self)
		self.vm = VmModel.get_vm(id)
		self.backups = BackupModel.get_vms_backups(id)



