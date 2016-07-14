from flask import Flask
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config.from_pyfile('app.cfg')
mongo = PyMongo(app, config_prefix='MONGO')

import models, views
