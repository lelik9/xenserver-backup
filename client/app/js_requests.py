# coding=utf-8
from __future__ import print_function
import json
from flask import request

from app import app
from controller import HostController


def response(result=None, resp_type='success'):
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