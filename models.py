#encoding: utf-8

# BSD license
# Written by Santiego(santiego@foxmail.com)

from exts import db, get_site_title, exts_verify_link, judge_url_type
from datetime import datetime
from config import USER_CODE, APP_CONFIG
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request
import hashlib
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


tabel_voters = db.Table('votes',
    db.Column('voter_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('voted_id', db.Integer, db.ForeignKey('answer.id'))
)

tabel_theme = db.Table('themes',
    db.Column('theme_id', db.Integer, db.ForeignKey('theme.id')),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'))
)

table_tag_to_question = db.Table('table_tag_to_question',
                                 db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                                 db.Column('question_id', db.Integer, db.ForeignKey('question.id')))

table_user_to_tag = db.Table('table_user_to_tag',
                             db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                             db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(128), nullable=False, unique=True)
    username = db.Column(db.Unicode(128), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    pw_hash = db.Column(db.String(128))
    avatar_hash = db.Column(db.String(32))
    desc = db.Column(db.UnicodeText, nullable=True, default=u"还没个人介绍呢")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_time = db.Column(db.DateTime, default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users'))

    confirmed = db.Column(db.Boolean, default=False)
    msg_unread = db.Column(db.Boolean, default=False)

    tags = db.relationship('Tag', secondary=table_user_to_tag,
                           backref=db.backref('users', lazy='dynamic'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == APP_CONFIG['APP_ROOT']:
                self.role = Role.query.filter_by(type=USER_CODE['root']).first()
            else:
                self.role = Role.query.filter_by(type=USER_CODE['email_not_pass']).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        launcher = Question(title=u"我的快速启动", desc=u"在此添加、删除、排序您的快速启动项", author=self, private=True)
        Theme.query.filter_by(name=APP_CONFIG['THEME_NAME_LAUNCHER']).first_or_404().questions.append(launcher)
        db.session.add(launcher)
        db.session.commit()

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.commit()
        return True

    @property
    def password(self):
        raise AttributeError('unable')

    @password.setter
    def password(self, password):
        self.pw_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.pw_hash, password)

    @staticmethod
    def register_available(email):
        if User.query.filter_by(email=email).first() is not None:
            return False
        return True

    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_email_or_404(email):
        return User.query.filter_by(email=email).first_or_404()

    @staticmethod
    def get_user_by_id(id):
        return User.query.filter_by(id=id).first()

    @staticmethod
    def get_user_by_id_or_404(id):
        return User.query.filter_by(id=id).first_or_404()

    @staticmethod
    def delete_user_from_email_complete(email):
        user = User.get_user_by_email(email)
        if user is None:
            return False
        for item in Question.query.filter_by(author=user).all():
            item.delete_answers()
            db.session.delete(item)
        db.session.delete(user)
        db.session.commit()
        return True

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def get_id_from_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return data.get('confirm')

    def get_follow_tag_question(self):
        query = db.session.query(Question)
        query = query.filter(Question.tags.any(Tag.users.any(User.id == self.id)))
        return query

    def hav_tag(self, name):
        if self.tags.filter_by(name=name).count() > 0:
            return True
        return False

    def add_tag(self, name):
        if self.hav_tag(name):
            return
        self.tags.append(Tag.get_or_create(name))

    def remove_tag(self, name):
        if self.hav_tag(name):
            self.tags.remove(Tag.get_or_create(name))

    def __repr__(self):
        return '<User %r %r>' % (self.username, self.email)


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Integer, default=USER_CODE['email_not_pass'])
    desc = db.Column(db.UnicodeText, nullable=True)

    def __repr__(self):
        return '<Role %r>' % self.type

    @staticmethod
    def load_roles():
        roles = {
            Role(type=USER_CODE['root'], desc=u"超级管理员"),
            Role(type=USER_CODE['admin'], desc=u"管理员"),
            Role(type=USER_CODE['email_not_pass'], desc=u"注册用户未激活邮箱"),
            Role(type=USER_CODE['common'], desc=u"普通用户"),
            Role(type=USER_CODE['bad_guy'], desc=u"封禁用户")
        }
        for item in roles:
            db.session.add(item)
        db.session.commit()


class Theme(db.Model):
    __tablename__ = 'theme'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.UnicodeText, nullable=False)
    desc = db.Column(db.UnicodeText, default=u"rt")

    questions = db.relationship('Question', secondary=tabel_theme,
                             backref=db.backref('themes', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Theme %r>' % self.name

    @staticmethod
    def load_themes():
        themes = {Theme(name=APP_CONFIG['THEME_NAME_GUIDE'], desc=u"互联网生存指南"),
                  Theme(name=APP_CONFIG['THEME_NAME_LAUNCHER'], desc=u"用户的快速启动"),
                  Theme(name=APP_CONFIG['THEME_NAME_NORMAL'], desc=u"普通可上架主题"),
                  Theme(name=APP_CONFIG['THEME_NAME_Q'], desc=u"未解决的问题"),
                  Theme(name=APP_CONFIG['THEME_NAME_PRIVATE'], desc=u"私用主题")}
        for item in themes:
            db.session.add(item)
        db.session.commit()


class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.UnicodeText, nullable=False)
    desc = db.Column(db.UnicodeText, default=u"rt")
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    vote = db.Column(db.Integer, default=0)
    private = db.Column(db.Boolean, default=False)

    author = db.relationship('User', backref=db.backref('questions', lazy='dynamic'))

    @staticmethod
    def get_question_by_title(title):
        return Question.query.filter_by(title=title).first()

    @staticmethod
    def get_question_by_id(id):
        return Question.query.filter_by(id=id).first()

    def vote_updata(self):
        if self.answers.count() == 0:
            return
        if self.private:
            self.vote = 0
            return
        temp = self.answers.first().vote
        for item in self.answers.all():
            temp = max(temp, item.vote)
        self.vote = temp

    def is_belong_to_theme(self, name):
        if self.themes.filter_by(name=name).count() > 0:
            return False
        return True

    def delete_answers(self):
        for item in self.answers.all():
            item.delete_comments()
            db.session.delete(item)

    def __repr__(self):
        return '<Question %r>' % self.title


class Answer(db.Model):
    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    desc = db.Column(db.UnicodeText, nullable=False)
    link = db.Column(db.UnicodeText, nullable=False)
    link_title = db.Column(db.UnicodeText)
    link_type = db.Column(db.Text, default='link')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    vote = db.Column(db.Integer, default=0)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    author = db.relationship('User', backref=db.backref('answers', lazy='dynamic'))
    question = db.relationship('Question', backref=db.backref('answers', lazy='dynamic'))

    voters = db.relationship('User', secondary=tabel_voters,
                             backref=db.backref('voted_answers', lazy='dynamic'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(Answer, self).__init__(**kwargs)
        if self.link_title is None:
            self.link_title = get_site_title(self.link)
        self.link_type = judge_url_type(self.link)

    def hav_vote(self, user):
        return self.voters.filter(tabel_voters.c.voter_id == user.id).count() > 0

    def motion_vote(self, user):
        if not self.hav_vote(user):
            self.voters.append(user)
        # Attention! -> db.session.commit()

    def delete_comments(self):
        for item in self.comments.all():
            db.session.delete(item)

    @staticmethod
    def verify_link(link):
        if exts_verify_link(link):
            return True
        else:
            return False

    @staticmethod
    def get_answer_by_id(id):
        return Answer.query.filter_by(id=id).first()

    @staticmethod
    def upgrade_for_link_type():
        answers = Answer.query.all()
        for answer in answers:
            answer.link_type = judge_url_type(answer.link)
        db.session.commit()

    def __repr__(self):
        return '<Answer %r>' % self.link_title


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.UnicodeText, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('comments', lazy='dynamic'))
    author = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))

    def __repr__(self):
        return '<Comment %r>' % self.content


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.UnicodeText, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', secondary=table_tag_to_question,
                                backref=db.backref('tags', lazy='dynamic'), lazy='dynamic')

    @staticmethod
    def get_or_create(name):
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()
        return tag

    def hav_question(self, question):
        if self.questions.filter_by(id=question.id).count() > 0:
            return True
        return False

    def add_to_tag(self, question):
        self.questions.append(question)

    def remove_from_tag(self, question):
        if self.hav_question(question):
            self.questions.remove(question)

    def __repr__(self):
        return '<Tag %r>' % self.name




class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.UnicodeText, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    addressee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    addressee = db.relationship('User', backref=db.backref('msgs', lazy='dynamic'))

    @staticmethod
    def send_message(addressee, content):
        msg = Message(content=content, addressee=addressee)
        #msg_root = Message(content=content,
        #                   addressee=User.query.filter_by(email=APP+CONFIG['APP_ROOT']).first_or_404())
        addressee.msg_unread = True
        db.session.add(msg)
        #db.session.add(msg_root)
        db.session.commit()

    def __repr__(self):
        return '<Message %r>' % self.content

# BSD license
# Written by Santiego(santiego@foxmail.com)


