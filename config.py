#encoding: utf-8

import os

DEBUG = True

SECRET_KEY = '...'

DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = '...'
HOST = '127.0.0.1'
PORT = '3306'
DATABASE = 'll'

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8mb4".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = 'smtp.ym.163.com'
MAIL_PORT = '994'
MAIL_USE_SSL = True
MAIL_USE_TLS = False
MAIL_USERNAME = "..."
MAIL_PASSWORD = "..."
APP_MAIL_SUBJECT_PREFIX = u"... - "
APP_MAIL_SENDER = u"...团队", "..."


USER_CODE = {
    'root': 0,
    'admin': 1,
    'common': 2,
    'email_not_pass': 3,
    'bad_guy': 4
}

MESSAGE_BOX_CN = {
    'pw_not_match': u"两次输入的密码不匹配",
    'register_not_available': u"无法注册，可能邮箱已被注册或无权限",
    'register_success': u"注册成功，请登录",
    'login_fail_email_not_exist': u"不存在此用户，请核对邮箱地址",
    'login_fail_pw': u"密码错误",
    'login_success': u"欢迎回来",
    'login_fail_bad_guy': u"您的账号已被封禁，请联系管理员",
    'logout_success': u"已注销账户",
    'link_fail': u"链接存在问题，请核对",
    'link_fail_same': u"已存在完全相同的分享，无法再次分享",
    'write_success': u"分享成功",
    'login_required': u"请先登录",
    'email_not_pass': u"您还未验证邮箱，请先验证邮箱",
    'question_fail_same': u"已存在相同问题，无法创建问题",
    'question_success': u"已创建问题，有任何消息我们会第一时间通知您",
    'edit_desc_fail': u"抱歉，无法修改",
    'edit_desc_success': u"修改成功",
    'edit_pw_success': u"密码修改成功",
    'del_success': u"删除成功",
    'email_confirm_success': u"账户激活成功",
    'email_confirm_have': u"账户已激活",
    'email_confirm_fail': u"账户激活失败，请重试",
    'email_prefix': u"激活您在...的账户",
    'email_prefix_pw_back': u"找回您在...的密码",
    'email_prefix_report': u"报告",
    'email_prefix_comment': u"有人回复了您分享的链接！",
    'email_prefix_welcome': u"欢迎加入...！",
    'email_prefix_new_link': u"您关注的主题有了新链接",
    'confirm_info': u"用于激活您的账号的链接已发至您的邮箱，若没有看到，请将lianglian.site将入到邮箱域名白名单",
    'confirm_info_pw_back': u"用于重置密码的链接已发至您的邮箱，若没有看到，请直接搜索邮件，关键字：...",
    'confirm_fail': u"令牌已过期，请重试",
    'pw_back_success': u"密码重置成功，请登录",
    'msg_unread': u"您有一条新消息未读",
    'email_too_frequently_fail': u"发送邮件冷却时间未到，请稍等",
    'report_success': u"报告成功，感谢您的反馈",
    'tag_del_success': u"标签删除成功"
}

APP_CONFIG = {
    'APP_ROOT': os.environ.get('APP_ROOT'),

    'POSTS_PER_PAGE': 5,
    'POSTS_PRE_PAGE_INDEX': 9,
    'POSTS_PRE_PAGE_EXPLORE': 40,
    'POSTS_PRE_PAGE_SEARCH': 5,
    'POSTS_PRE_PAGE_MSG': 15,
    'POSTS_PRE_PAGE_USER': 3,
    'POSTS_PRE_PAGE_TAG': 20,
    'TAGS_PRE_PAGE': 40,
    'TAGS_PRE_PAGE_EXPLORE': 40,
    'THEME_NAME_GUIDE': u"GUIDE",
    'THEME_NAME_LAUNCHER': u"LAUNCHER",
    'THEME_NAME_NORMAL': u"NORMAL",
    'THEME_NAME_PRIVATE': u"PRIVATE",
    'THEME_NAME_Q': u"QUESTION",
    'ORDER_BY_TIME': 1,
    'ORDER_BY_VOTE': 2,
    'ORDER_BY_Q': 3
}