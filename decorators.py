# BSD license
# Written by Santiego(santiego@foxmail.com)

from functools import wraps
from flask import flash, redirect, session, url_for, request, g, abort, jsonify
from config import MESSAGE_BOX_CN, USER_CODE
import urllib
import datetime


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id'):
            return func(*args, **kwargs)
        else:
            flash(MESSAGE_BOX_CN['login_required'])
            return redirect(url_for('login', from_=urllib.quote(request.url)))

    return wrapper


def login_required_ajax(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id'):
            return func(*args, **kwargs)
        else:
            return jsonify({'state': 'LOGIN_REQUIRED'})

    return wrapper


def login_required_only_post(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id') or request.method == 'GET':
            return func(*args, **kwargs)
        else:
            flash(MESSAGE_BOX_CN['login_required'])
            return redirect(url_for('login', from_=urllib.quote(request.url)))

    return wrapper


def confirm_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id') is None:
            flash(MESSAGE_BOX_CN['login_required'])
            return redirect(url_for('login', from_=urllib.quote(request.url)))
        if not g.user.confirmed:
            flash(MESSAGE_BOX_CN['email_not_pass'])
            return redirect(url_for('view_confirm'))
        return func(*args, **kwargs)

    return wrapper


def email_protected(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('email_protected') is None:
            session['email_protected'] = datetime.datetime.now()
            session.permanent = True
            return func(*args, **kwargs)
        else:
            if (datetime.datetime.now()-session.get('email_protected')).seconds <= 60:
                flash(MESSAGE_BOX_CN['email_too_frequently_fail'])
                return redirect(request.referrer) or redirect(url_for('index'))
            return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id') and \
                (g.user.role.type == USER_CODE['admin'] or g.user.role.type == USER_CODE['root']):
            return func(*args, **kwargs)
        else:
            abort(403)

    return wrapper

# BSD license
# Written by Santiego(santiego@foxmail.com)

