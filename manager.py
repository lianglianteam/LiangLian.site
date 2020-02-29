#encoding: utf-8

from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from app import app
from exts import db
from models import User, Role, Answer, Question, Theme, Comment, Tag, Message

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def load():
    Role.load_roles()
    Theme.load_themes()


@manager.command
def upgrade_for_link_type():
    Answer.upgrade_for_link_type()


@manager.command
def delete_user(email):
    if User.delete_user_from_email_complete(email):
        print 'Done.'
    else:
        print 'User <' + email + '> does not exist'


@manager.command
def users():
    for item in User.query.all():
        print item


if __name__ == "__main__":
    manager.run()
