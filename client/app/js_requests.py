# coding=utf-8
from flask import request

from app import app


@app.route('/add_host', methods=['GET', 'POST'])
def add_host():
    ip = request.form['ip']
    login = request.form['login']
    password = request.form['password']

    print(login)
