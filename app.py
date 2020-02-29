#encoding: utf-8

# BSD license
# Written by Santiego(santiego@foxmail.com)

from flask import Flask, request, render_template, redirect, url_for, flash, session, g, abort, jsonify, send_from_directory
from sqlalchemy import and_
import config
from config import USER_CODE, MESSAGE_BOX_CN, APP_CONFIG
from models import User, Theme, Question, Comment, Answer, Message, Tag
from exts import db, moment, mail, send_email

from datetime import datetime
from decorators import login_required, login_required_only_post, confirm_required, email_protected, admin_required, login_required_ajax
import urllib

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
moment.init_app(app)
mail.init_app(app)


@app.route('/')
def index():
    page = int(request.args.get('page') or 1)
    anchor = None
    if page != 1:
        anchor = 'follow'
    if session.get('user_id'):
        launcher = g.my_theme_launcher.questions.filter_by(author=g.user).first_or_404()
        launcher_list = launcher.answers.order_by(Answer.vote.desc()).all()
        questions_guide = g.my_theme_guide.questions.order_by(Question.create_time.desc()).limit(
            APP_CONFIG['POSTS_PRE_PAGE_INDEX']).all()
        questions_last = g.my_theme_normal.questions.order_by(Question.create_time.desc()).limit(
            APP_CONFIG['POSTS_PRE_PAGE_INDEX']).all()
        questions_follow = g.user.get_follow_tag_question().order_by(Question.create_time.desc()).paginate(page,
                                                                                                           APP_CONFIG[
                                                                                                               'POSTS_PRE_PAGE_INDEX'],
                                                                                                           False)
        tags_list = Tag.query.order_by(Tag.create_time.desc()).limit(APP_CONFIG['TAGS_PRE_PAGE']).all()
        return render_template('index.html', questions_last=questions_last, questions_guide=questions_guide,
                               launcher=launcher, launcher_list=launcher_list, questions_follow=questions_follow,
                               tags_list=tags_list, anchor=anchor)
    else:
        questions_last = g.my_theme_normal.questions.order_by(Question.create_time.desc()).limit(
            APP_CONFIG['POSTS_PRE_PAGE_INDEX']).all()
        questions_guide = g.my_theme_guide.questions.order_by(Question.create_time.desc()).limit(
            APP_CONFIG['POSTS_PRE_PAGE_INDEX']).all()
        tags_list = Tag.query.order_by(Tag.create_time.desc()).limit(APP_CONFIG['TAGS_PRE_PAGE']).all()
        return render_template('index.html', questions_last=questions_last, questions_guide=questions_guide,
                               tags_list=tags_list)


@app.route('/explore')
@app.route('/explore/<int:page>')
def explore(page=1):
    type = int(request.args.get('t') or 1)
    if type == APP_CONFIG['ORDER_BY_TIME']:
        questions = g.my_theme_normal.questions.order_by(Question.create_time.desc()).paginate(page, APP_CONFIG[
            'POSTS_PRE_PAGE_EXPLORE'], False)
    if type == APP_CONFIG['ORDER_BY_VOTE']:
        questions = g.my_theme_normal.questions.order_by(Question.vote.desc()).paginate(page, APP_CONFIG[
            'POSTS_PRE_PAGE_EXPLORE'], False)
    #if type == APP_CONFIG['ORDER_BY_Q']:
    #    questions = g.my_theme_normal.questions.filter(Question.answers.count() == 0).order_by(
    #        Question.create_time.desc()).paginate(page, APP_CONFIG['POSTS_PRE_PAGE_EXPLORE'], False)
    tags_list = Tag.query.order_by(Tag.create_time.desc()).limit(APP_CONFIG['TAGS_PRE_PAGE_EXPLORE']).all()
    return render_template('explore.html', questions=questions, tags_list=tags_list)


@app.route('/guide')
@app.route('/guide/<int:page>')
def guide(page=1):
    questions = g.my_theme_guide.questions.order_by(Question.vote.desc()).paginate(page,
                                                                                   APP_CONFIG['POSTS_PRE_PAGE_EXPLORE'],
                                                                                   False)
    return render_template('guide.html', questions=questions)


@app.route('/search')
def search():
    word = request.args.get('word')
    anchor = 'title'
    page = int(request.args.get('page') or 1)
    if page != 1:
        anchor = 'link'
    page_questions = int(request.args.get('page_questions') or 1)
    if page_questions != 1:
        anchor = 'theme'
    page_authors = int(request.args.get('page_authors') or 1)
    if page_authors != 1:
        anchor = 'user'
    if word is None:
        abort(404)
    words = unicode(word).split()
    questions = Question.query.filter(and_(*[Question.title.contains(w) for w in words])).paginate(page_questions, APP_CONFIG[
        'POSTS_PRE_PAGE_SEARCH'], False)
    answers = Answer.query.filter(and_(*[Answer.desc.contains(w) for w in words])).paginate(page, APP_CONFIG[
        'POSTS_PRE_PAGE_SEARCH'], False)
    authors = User.query.filter(and_(*[User.username.contains(w) for w in words])).paginate(page_authors, APP_CONFIG[
        'POSTS_PRE_PAGE_SEARCH'], False)
    return render_template('search.html', word=word, questions=questions, answers=answers, authors=authors, anchor=anchor)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/msg')
@app.route('/msg/<int:page>')
@login_required
def msg(page=1):
    msgs = g.user.msgs.order_by(Message.create_time.desc()).paginate(page, APP_CONFIG['POSTS_PRE_PAGE_MSG'], False)
    g.user.msg_unread = False
    db.session.commit()
    return render_template('msg.html', msgs=msgs)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form.get('email')
        pw = request.form.get('pw')
        remember_me = request.form.get('rememberMe')  # off=None
        if email is None or pw is None:
            abort(403)
        user = User.get_user_by_email(email)
        if user is None:
            flash(MESSAGE_BOX_CN['login_fail_email_not_exist'])
            return render_template('login.html')
        if not user.verify_password(pw):
            flash(MESSAGE_BOX_CN['login_fail_pw'])
            return render_template('login.html', email=email)

        session['user_id'] = user.id
        if remember_me:
            session.permanent = True
        flash(MESSAGE_BOX_CN['login_success'])
        return redirect(url_for('index')) if request.args.get('from_') is None else redirect(urllib.unquote(request.args.get('from_')))


@app.route('/logout')
@login_required
def logout():
    session['user_id'] = None
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form.get('username')
        email = request.form.get('email')
        desc = request.form.get('desc')
        pw1 = request.form.get('password1')
        pw2 = request.form.get('password2')
        if username is None or email is None or pw1 is None:
            abort(403)
        if pw1 != pw2:
            flash(MESSAGE_BOX_CN['pw_not_match'])
            return render_template('register.html', username=username, email=email, desc=desc)
        if not User.register_available(email):
            flash(MESSAGE_BOX_CN['register_not_available'])
            return render_template('register.html', username=username, pw1=pw1, pw2=pw2, desc=desc)
        cur_user = User(username=username, password=pw1, email=email, desc=desc)
        db.session.add(cur_user)
        db.session.commit()
        Message.send_message(cur_user, render_template('msg/msg_item_welcome.html', user_=cur_user))
        # send_email(cur_user.email, MESSAGE_BOX_CN['email_prefix_welcome'], 'email/msg_welcome', user_=cur_user)
        flash(MESSAGE_BOX_CN['register_success'])
        return redirect(url_for('login'))


@app.route('/write_answer', methods=['GET', 'POST'])
@login_required
@confirm_required
def write_answer():
    if request.method == 'GET':
        question_id = request.args.get('question')
        link = request.args.get('link') or ''
        if question_id is not None:
            return render_template('write_answer.html', disable=True, question=Question.query.filter_by(id=question_id).first_or_404().title, link=link)
        return render_template('write_answer.html', link=link)
    else:
        question_get = request.form.get('question')
        question_desc = request.form.get('question_desc')
        link = request.form.get('link')
        desc = request.form.get('desc')
        private = request.form.get('private')  # off=None
        tags = unicode(request.form.get('tags')).split(',')

        if (question_get is None and request.args.get('question') is None) or desc is None or link is None:
            abort(403)
        author = g.user
        if question_get == u"我的快速启动":
            question = Question.query.filter_by(id=request.args.get('question'), author=author).first_or_404()
        else:
            question = Question.query.filter_by(id=request.args.get('question')).first()
        if question is None:
            question = Question(title=question_get, author=author, desc=question_desc)
            if private is None:
                g.my_theme_normal.questions.append(question)
            else:
                g.my_theme_normal.questions.append(question)
                question.private = True
            db.session.add(question)
            db.session.commit()
        else:
            if question.private and g.user.id != question.author.id:
                abort(403)
        for tag in tags:
            if tag is not None:
                Tag.get_or_create(tag).add_to_tag(question)
        if not Answer.verify_link(link):
            flash(MESSAGE_BOX_CN['link_fail'])
            return render_template('write_answer.html', question=question_get, link=link, desc=desc, question_desc=question_desc)
        if Answer.query.filter_by(link=link, question=question, desc=desc).first() is not None:
            flash(MESSAGE_BOX_CN['link_fail_same'])
            return render_template('write_answer.html', question=question_get, link=link, desc=desc, question_desc=question_desc)
        answer = Answer(link=link, desc=desc, author=author, question=question)
        db.session.add(answer)
        db.session.commit()
        if g.user.id != question.author.id:
            Message.send_message(question.author,
                                 render_template('msg/msg_item_answer.html', sender=g.user, answer=answer, question=question))
            send_email(question.author.email, MESSAGE_BOX_CN['email_prefix_new_link'], 'email/msg_answer',
                       sender=g.user, answer=answer)
        flash(MESSAGE_BOX_CN['write_success'])
        return redirect(url_for('view_question', id=answer.question.id, _anchor="answer-"+str(answer.id)))


@app.route('/write_question', methods=['GET', 'POST'])
@login_required
@confirm_required
def write_question():
    if request.method == 'GET':
        return render_template('write_question.html')
    else:
        title = request.form.get('title')
        desc = request.form.get('desc')
        tags = unicode(request.form.get('tags')).split(',')
        if title is None or desc is None:
            abort(403)
        if Question.query.filter_by(title=title).first() is not None:
            flash(MESSAGE_BOX_CN['question_fail_same'])
            return render_template('write_question.html', title=title, desc=desc)
        question = Question(title=title, desc=desc, author=g.user)
        g.my_theme_normal.questions.append(question)
        g.my_theme_question.questions.append(question)
        for tag in tags:
            if tag is not None:
                Tag.get_or_create(tag).add_to_tag(question)
        db.session.add(question)
        db.session.commit()
        question = Question.query.filter_by(title=title, desc=desc, author=g.user).first()
        flash(MESSAGE_BOX_CN['question_success'])
        return redirect(url_for('view_question', id=question.id))


'''
@app.route('/answer/<int:id>', methods=['GET', 'POST'])
@login_required_only_post
def view_answer(id):
    answer = Answer.query.filter_by(id=id).first_or_404()
    question = answer.question
    if request.method == 'POST':
        content = request.form.get('comment')
        comment = Comment(content=content, author=g.user, answer=answer)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('view_answer', id=id, _anchor="comment-"+str(comment.id)))

    return render_template('view_answer.html', answer=answer, question=question)
'''


@app.route('/question/<int:id>/<int:page>', methods=['GET', 'POST'])
@app.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required_only_post
def view_question(id, page=1):
    question = Question.query.filter_by(id=id).first_or_404()
    answers_query = Answer.query.filter_by(question=question).order_by(Answer.vote.desc())
    answers = answers_query.paginate(page, APP_CONFIG['POSTS_PER_PAGE'], False)
    if request.method == 'POST':
        content = request.form.get('comment')
        cur_answer = Answer.query.filter_by(id=request.form.get('answer_id')).first_or_404()
        comment = Comment(content=content, author=g.user, answer=cur_answer)
        Message.send_message(cur_answer.author, render_template('msg/msg_item_comment.html', sender=g.user, answer=cur_answer, text=content))
        if g.user.id != cur_answer.author.id:
            send_email(cur_answer.author.email, MESSAGE_BOX_CN['email_prefix_comment'], 'email/msg_comment', sender=g.user, answer=cur_answer, text=content)
        db.session.add(comment)
        db.session.commit()
        return render_template('view_question.html', answers=answers, question=question, _anchor="comment-"+str(comment.id))

    return render_template('view_question.html', answers=answers, question=question)


@app.route('/user/<int:id>')
def view_user(id):
    user = User.query.filter_by(id=id).first_or_404()
    anchor = None
    page = int(request.args.get('page') or 1)
    if page != 1:
        anchor = 'link'
    page_questions = int(request.args.get('page_questions') or 1)
    if page_questions != 1:
        anchor = 'theme'
    page_authors = int(request.args.get('page_authors') or 1)
    questions = g.my_theme_normal.questions.filter_by(author=user).order_by(Question.create_time.desc()).paginate(page_questions,
                                                               APP_CONFIG[
                                                                   'POSTS_PRE_PAGE_USER'],
                                                               False)
    answers = Answer.query.filter_by(author=user).order_by(Answer.create_time.desc()).paginate(page, APP_CONFIG[
        'POSTS_PRE_PAGE_USER'], False)
    point = answers.total + questions.total * 0.1
    tags_list = user.tags.all()
    return render_template('view_user.html', user_=user, point=point, questions=questions, answers=answers,
                           anchor=anchor, tags_list=tags_list)


@app.route('/tags')
def tags():
    page = request.args.get('page') or 1
    tags = Tag.query.order_by(Tag.create_time.desc()).paginate(page,
                                                               APP_CONFIG[
                                                                   'POSTS_PRE_PAGE_TAG'],
                                                               False)
    return render_template('tags.html', tags=tags)


@app.route('/tag/<int:id>')
def view_tag(id):
    page = request.args.get('page') or 1
    tag = Tag.query.filter_by(id=id).first_or_404()
    questions = tag.questions.order_by(Question.create_time.desc()).paginate(page,
                                                                             APP_CONFIG[
                                                                                 'POSTS_PRE_PAGE_TAG'],
                                                                             False)
    return render_template('view_tag.html', tag=tag, questions=questions)


@app.route('/edit_user_desc/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user_desc(id):
    if request.method == 'GET':
        return render_template('edit_user_desc.html', desc=User.query.filter_by(id=id).first_or_404().desc)
    else:
        if id != session.get('user_id') and g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
            flash(MESSAGE_BOX_CN['edit_desc_fail'])
            return redirect(url_for('index'))
        desc = request.form.get('desc')
        user = User.query.filter_by(id=id).first_or_404()
        user.desc = desc
        db.session.commit()
        flash(MESSAGE_BOX_CN['edit_desc_success'])
        return redirect(url_for('view_user', id=id))


@app.route('/edit_pw', methods=['GET', 'POST'])
@login_required
def edit_pw():
    if request.method == 'GET':
        return render_template('edit_pw.html')
    else:
        pw_origin = request.form.get('pw_origin')
        pw = request.form.get('pw')
        pw2 = request.form.get('pw2')
        if pw_origin is None or pw is None or pw2 is None:
            abort(403)
        if pw != pw2:
            flash(MESSAGE_BOX_CN['pw_not_match'])
            return render_template('edit_pw.html', pw_origin=pw_origin)
        if not g.user.verify_password(pw_origin):
            flash(MESSAGE_BOX_CN['login_fail_pw'])
            return render_template('edit_pw.html', pw=pw, pw2=pw2)
        user = g.user
        user.password = pw
        db.session.commit()
        flash(MESSAGE_BOX_CN['edit_pw_success'])
        return redirect(url_for('index'))


@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'GET':
        theme = request.args.get('theme')
        if theme is None:
            return render_template('report.html')
        else:
            return render_template('report.html', theme=theme, disable=True)
    else:
        theme = request.form.get('theme')
        body = request.form.get('report')
        if theme is None or body is None:
            abort(403)
        Message.send_message(addressee=User.get_user_by_email_or_404(APP_CONFIG['APP_ROOT']),
                             content=render_template('msg/msg_item_report.html', theme=theme, body=body))
        send_email(APP_CONFIG['APP_ROOT'], MESSAGE_BOX_CN['email_prefix_report'], 'email/msg_report', theme=theme, body=body)
        flash(MESSAGE_BOX_CN['report_success'])
        return redirect(request.referrer or url_for('index'))


@app.route('/motion/vote-up/<int:id>')
@login_required
def motion_vote_up(id):
    answer = Answer.query.filter_by(id=id).first_or_404()
    if answer.question.private:
        if g.user.id != answer.author.id:
            abort(403)
        answer.vote += 1
        answer.question.vote_updata()
        db.session.commit()
        return redirect(url_for('view_question', id=answer.question.id, _anchor="answer-" + str(answer.id)))
    else:
        if answer.hav_vote(g.user):
            abort(403)
        answer.vote += 1
        if g.user.id != answer.author.id:
            Message.send_message(answer.author, render_template('msg/msg_item_vote.html', sender=g.user, answer=answer))
        answer.motion_vote(g.user)
        answer.question.vote_updata()
        db.session.commit()
        return redirect(url_for('view_question', id=answer.question.id, _anchor="answer-"+str(answer.id)))


@app.route('/motion/vote-down/<int:id>')
@login_required
def motion_vote_down(id):
    answer = Answer.query.filter_by(id=id).first_or_404()
    if answer.question.private:
        if g.user.id != answer.author.id:
            abort(403)
        answer.vote -= 1
        answer.question.vote_updata()
        db.session.commit()
        return redirect(url_for('view_question', id=answer.question.id, _anchor="answer-" + str(answer.id)))
    else:
        if answer.hav_vote(g.user):
            abort(403)
        answer.vote -= 1
        answer.motion_vote(g.user)
        answer.question.vote_updata()
        db.session.commit()
        return redirect(url_for('view_question', id=answer.question.id, _anchor="answer-"+str(answer.id)))


@app.route('/motion/del-answer/<int:id>')
@login_required
def motion_del_answer(id):
    answer = Answer.query.filter_by(id=id).first_or_404()
    question_id = answer.question.id
    if g.user.id != answer.author.id and g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
        abort(403)
    answer.delete_comments()
    db.session.delete(answer)
    db.session.commit()
    flash(MESSAGE_BOX_CN['del_success'])
    return redirect(url_for('view_question', id=question_id))


@app.route('/motion/del-comment/<int:id>')
@login_required
def motion_del_comment(id):
    comment = Comment.query.filter_by(id=id).first_or_404()
    question_id = comment.answer.question.id
    answer_id = comment.answer.id
    if g.user.id != comment.author.id and g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash(MESSAGE_BOX_CN['del_success'])
    return redirect(url_for('view_question', id=question_id, _anchor="answer-"+str(answer_id)))


@app.route('/motion/del-question/<int:id>')
@login_required
def motion_del_question(id):
    question = Question.query.filter_by(id=id).first_or_404()
    if g.user.id != question.author.id and g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
        abort(403)
    db.session.delete(question)
    for answer in question.answers.all():
        db.session.delete(item)
        for item in answer.comments.all():
            db.session.delete(item)

    db.session.commit()
    flash(MESSAGE_BOX_CN['del_success'])
    return redirect(url_for('index'))


@app.route('/motion/add-to-theme/<string:name>/<int:id>')
@login_required
def motion_add_to_theme(name, id):
    if g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
        abort(403)
    theme = Theme.query.filter_by(name=name).first_or_404()
    theme.questions.append(Question.query.filter_by(id=id).first_or_404())
    db.session.commit()
    return redirect(url_for('view_question', id=id))


@app.route('/motion/del-to-theme/<string:name>/<int:id>')
@login_required
def motion_del_to_theme(name, id):
    if g.user.role.type != USER_CODE['root'] and g.user.role.type != USER_CODE['admin']:
        abort(403)
    theme = Theme.query.filter_by(name=name).first_or_404()
    theme.questions.remove(Question.query.filter_by(id=id).first_or_404())
    db.session.commit()
    return redirect(url_for('view_question', id=id))


@app.route('/motion/edit_user_role/<int:id>/<int:role>')
@admin_required
def motion_edit_user_role(id, role):
    if id == User.get_user_by_email_or_404(APP_CONFIG['APP_ROOT']).id:
        abort(403)
    user = User.query.filter_by(id=id).first_or_404()
    user.role.type = role
    if role != USER_CODE['email_not_pass']:
        user.confirmed = True
    db.session.commit()
    return redirect(url_for('view_user', id=id))


@app.route('/motion/del_user_msg/<int:id>')
@login_required
def motion_del_user_msg(id):
    user = User.query.filter_by(id=id).first_or_404()
    if g.user.id != user.id and g.user.role.type != USER_CODE['root']:
        abort(403)
    for item in user.msgs.all():
        db.session.delete(item)
    db.session.commit()
    return redirect(url_for('msg'))


@app.route('/motion/add_tag_to_user/<string:name>')
@login_required
def motion_add_tag_to_user(name):
    g.user.add_tag(name)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/motion/del_tag_from_user/<string:name>')
@login_required
def motion_del_tag_from_user(name):
    g.user.remove_tag(name)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/motion/del_tag/<int:id>')
@admin_required
def motion_del_tag(id):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash(MESSAGE_BOX_CN['tag_del_success'])
    return redirect(url_for('tags'))


@app.route('/motion/follow_tag', methods=['POST'])
@login_required_ajax
def motion_follow_tag():
    id = request.form.get('id')
    if id is None:
        abort(403)
    tag = Tag.query.filter_by(id=id).first_or_404()
    name = tag.name
    state = 'follow'
    if g.user.hav_tag(name):
        state = 'unfollow'
        g.user.remove_tag(name)
    else:
        g.user.add_tag(name)
    db.session.commit()
    cnt = tag.users.count()
    return jsonify({'state': 'success',
                    'now': state,
                    'cnt': str(cnt)})


@app.route('/motion/load_posts', methods=['POST'])
def motion_load_posts():
    req_type = request.form.get('type')
    page = int(request.form.get('page') or 2)
    per_page = int(request.form.get('per_page') or 2)
    if req_type is None or page is None:
        abort(405)
    posts = None
    has_nxt = False
    if req_type == 'questions_last':
        posts = g.my_theme_normal.questions.order_by(Question.create_time.desc()).paginate(page, per_page, False)
    if req_type == 'questions_follow':
        posts = g.user.get_follow_tag_question().order_by(Question.create_time.desc()).paginate(page, per_page, False)
    if req_type == 'questions_guide':
        posts = g.my_theme_guide.questions.order_by(Question.create_time.desc()).paginate(page, per_page, False)
    if req_type == 'questions_guide_best':
        posts = g.my_theme_guide.questions.order_by(Question.vote.desc()).paginate(page, per_page, False)

    if posts.has_next:
        has_nxt = True

    return jsonify({'posts': render_template('_questions_list_with_for.html', questions=posts),
                    'has_nxt': has_nxt})


@app.route('/motion/vote', methods=['POST'])
@login_required_ajax
def motion_vote():
    id = int(request.form.get('id') or 0)
    type = str(request.form.get('type') or 'up')
    answer = Answer.query.filter_by(id=id).first_or_404()
    if answer.question.private:
        return jsonify({'state': 'CAN_NOT'})

    if answer.hav_vote(g.user):
        return jsonify({'state': 'CAN_NOT'})
    if type == 'up':
        answer.vote += 1
        if g.user.id != answer.author.id:
            Message.send_message(answer.author, render_template('msg/msg_item_vote.html', sender=g.user, answer=answer))
    else:
        answer.vote -= 1
    answer.motion_vote(g.user)
    answer.question.vote_updata()
    db.session.commit()
    return jsonify({'state': 'success',
                    'vote': str(answer.vote)})


@app.route('/motion/jump')
def motion_jump():
    url = request.args.get('url')
    if url is None:
        return redirect(url_for('index'))
    return redirect(url)


@app.route('/view_confirm')
@login_required
def view_confirm():
    if g.user.confirmed:
        flash(MESSAGE_BOX_CN['email_confirm_have'])
        return redirect(request.referrer or url_for('index'))
    return render_template('view_confirm.html')


@app.route('/confirm/<token>')
@login_required
def confirm(token):
    if g.user.confirmed:
        return redirect(url_for('index'))
    if g.user.confirm(token):
        flash(MESSAGE_BOX_CN['email_confirm_success'])
        return redirect(url_for('index'))
    else:
        flash(MESSAGE_BOX_CN['email_confirm_fail'])
        return redirect(url_for('view_confirm'))


@app.route('/confirm')
@login_required
@email_protected
def send_confirm():
    token = g.user.generate_confirmation_token()
    send_email(g.user.email, MESSAGE_BOX_CN['email_prefix'], '/email/confirm', user=g.user, token=token)
    flash(MESSAGE_BOX_CN['confirm_info'])
    return redirect(url_for('view_confirm'))


@app.route('/view_pw_back', methods=['GET', 'POST'])
def view_pw_back():
    if request.method == 'GET':
        return render_template('view_pw_back.html')
    else:
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash(MESSAGE_BOX_CN['login_fail_email_not_exist'])
            return redirect(url_for('view_pw_back'))
        return redirect(url_for('pw_back', id=user.id))


@app.route('/pw_back_confirm/<token>', methods=['GET', 'POST'])
def pw_back_confirm(token):
    if request.method == 'GET':
        if session.get('user_id'):
            return redirect(url_for('index'))
        user_id = User.get_id_from_token(token)
        if user_id is None:
            flash(MESSAGE_BOX_CN['confirm_fail'])
            return redirect(url_for('view_pw_back'))
        if User.query.filter_by(id=user_id) is None:
            flash(MESSAGE_BOX_CN['login_fail_email_not_exist'])
            return redirect(url_for('view_pw_back'))

        return render_template('edit_pw_back.html')
    else:
        user_id = User.get_id_from_token(token)
        if user_id is None:
            flash(MESSAGE_BOX_CN['confirm_fail'])
            return redirect(url_for('view_pw_back'))
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            flash(MESSAGE_BOX_CN['login_fail_email_not_exist'])
            return redirect(url_for('view_pw_back'))

        pw = request.form.get('pw')
        pw2 = request.form.get('pw2')
        if pw is None:
            abort(403)
        if pw != pw2:
            flash(MESSAGE_BOX_CN['pw_not_match'])
            return render_template('view_pw_back.html')
        user.password = pw
        db.session.commit()
        flash(MESSAGE_BOX_CN['pw_back_success'])
        return redirect(url_for('login'))


@app.route('/pw_back/<int:id>')
@email_protected
def pw_back(id):
    user = User.query.filter_by(id=id).first()
    token = user.generate_confirmation_token()
    send_email(user.email, MESSAGE_BOX_CN['email_prefix_pw_back'], '/email/pw_back', user=user, token=token)
    flash(MESSAGE_BOX_CN['confirm_info_pw_back'])
    return redirect(url_for("index"))


@app.context_processor
def user_processor():
    ans = {'USER_CODE': USER_CODE,
           'APP_CONFIG': APP_CONFIG
           }
    user_id = session.get('user_id')
    if user_id:
        user = User.get_user_by_id(user_id)
        if user is None:
            return ans
        # user_launcher = g.my_theme_launcher.questions.filter_by(author=g.user).first_or_404()
        # ans.update(user=user, user_launcher=user_launcher)
        ans.update(user=user)
    return ans


@app.before_request
def before_request():
    user_id = session.get('user_id')
    if user_id:
        user = User.get_user_by_id(user_id)
        user.last_active_time = datetime.utcnow()
        db.session.commit()
        g.user = user
        if user.role.type == USER_CODE['bad_guy']:
            flash(MESSAGE_BOX_CN['login_fail_bad_guy'])
            session['user_id'] = None
            return redirect(url_for('index'))
    g.my_theme_normal = Theme.query.filter_by(name=APP_CONFIG['THEME_NAME_NORMAL']).first_or_404()
    g.my_theme_launcher = Theme.query.filter_by(name=APP_CONFIG['THEME_NAME_LAUNCHER']).first_or_404()
    g.my_theme_guide = Theme.query.filter_by(name=APP_CONFIG['THEME_NAME_GUIDE']).first_or_404()
    g.my_theme_question = Theme.query.filter_by(name=APP_CONFIG['THEME_NAME_Q']).first_or_404()


@app.route('/robots.txt')
def motion_static_file():
    return send_from_directory('static/data', request.path[1:])


@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', error=error), 500


@app.errorhandler(403)
def internal_error(error):
    db.session.rollback()
    return render_template('403.html', error=error), 403



if __name__ == '__main__':
    app.run()

# BSD license
# Written by Santiego(santiego@foxmail.com)

