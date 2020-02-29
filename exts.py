# BSD license
# Written by Santiego(santiego@foxmail.com)

from flask import current_app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail, Message

from threading import Thread
from lxml import etree
import urllib2, urllib, chardet
import datetime

db = SQLAlchemy()
moment = Moment()
mail = Mail()


def judge_url_type(url):
    download_type = {'magnet:?', 'thunder://', 'ed2k://', 'ftp://'}
    url = url.lower()
    download = False
    for pre in download_type:
        if url.startswith(pre):
            return pre
    return 'link'


def get_site_title(link):
    send_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Referer': link
    }
    try:
        response = urllib2.urlopen(urllib2.Request(link, headers=send_headers))
        title = etree.HTML(response.read().decode('utf-8')).xpath("/html/head/title")[0].text
    except:
        return link
    return title


def exts_verify_link(link):
    '''
    send_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Referer': link
    }
    try:
        urllib2.urlopen(urllib2.Request(link, headers=send_headers))
    except:
        return False
    '''
    return True


def send_async_email(app, to, subject, template_done_html, template_done_txt):
    with app.app_context():
        msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + subject,
                      sender=app.config['APP_MAIL_SENDER'], recipients=[to])
        msg.body = template_done_txt
        msg.html = template_done_html
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    template_done_html = render_template(template + '.html', **kwargs)
    template_done_txt = render_template(template + '.txt', **kwargs)
    thr = Thread(target=send_async_email, args=[app, to, subject, template_done_html, template_done_txt])
    thr.start()
    return thr

# BSD license
# Written by Santiego(santiego@foxmail.com)
