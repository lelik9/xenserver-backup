# coding=utf-8
from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
with app.app_context():
    app.config.from_pyfile('app.cfg')
    mongo = PyMongo(app, config_prefix='MONGO')

    from models import *
    HostsModel.set_db(mongo.db.hosts)
    VmModel.set_db(mongo.db.vm)
    BackupModel.set_db(mongo.db.backup)
    BackupStorageModel.set_db(mongo.db.backup_sr)

    import views
