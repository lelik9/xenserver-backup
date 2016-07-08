# coding=utf-8
import json
from flask import request

from app import app


@app.route('/host/', methods=['POST'])
def add_host():
    """

    :return:
    """
    ip = request.form['ip']
    login = request.form['login']
    password = request.form['password']

    return json.dumps({'message': 'Add host SUCCESS', 'type': 'success'})


@app.route('/host/', methods=['DELETE'])
def rm_host():
    """

    :return:
    """
    print(len(request.form))
    for a in request.form:
        print(a)
    return json.dumps({'message': 'Add host SUCCESS', 'type': 'success'})


@app.route('/backup/', methods=['POST'])
def backup_vm():
    """

    :return:
    """
    print(request.form)
    return 'success'