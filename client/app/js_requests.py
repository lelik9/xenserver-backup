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

    return 'success'


@app.route('/host/', methods=['DELETE'])
def rm_host():
    """

    :return:
    """
    id = request.form['id']
    return 'success'
