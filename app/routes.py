import datetime
import json
from flask import render_template, flash, redirect, url_for, request, jsonify, make_response, g
from app import app, db, photos, scheduler
from app.forms import LoginForm, RegistrationForm, SearchUserForm, EditProfileForm, AddTaskForm, \
    EmptyForm, ShowTaskForm, ResetPasswordRequestForm, ResetPasswordForm, UploadForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users, TypeTask, Priority, Status, Tasks, Complexity, Subscription, Category
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from pywebpush import webpush, WebPushException
from app.email import send_password_reset_email, send_email
from flask_babel import _, get_locale, lazy_gettext as _l
from dateutil.relativedelta import relativedelta
from onesignal_sdk.client import Client
import jwt
from time import time
import os
from bs4 import BeautifulSoup
from app.notify import NotifySend

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.is_authenticated and current_user.is_family(current_user):
        return redirect(url_for('tasks'))
    elif current_user.is_authenticated and not current_user.is_family(current_user):
        return redirect(url_for('user', username=current_user.username))
    return render_template('index.html', title=_('Home Page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = Users.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@app.route('/search_user', methods=['GET', 'POST'])
@login_required
def search():
    search_from = SearchUserForm()
    if search_from.validate_on_submit():
        user_partner = Users.query.filter_by(username=search_from.username.data).first()
        errors = {}  #dict for errors
        if user_partner is None:
            text_error = _('User %(username)s not found. Repeat search.', username=search_from.username.data)
            errors.update({'username': text_error})
            data = json.dumps(errors, ensure_ascii=True)
            return jsonify(data)
        if user_partner == current_user:
            errors.update({'username': _('You cannot create family only yourself!')})
            data = json.dumps(errors, ensure_ascii=True)
            return jsonify(data)
        if user_partner.is_family(user_partner) > 0:
            text_error = _('User %(username)s have family!', username=search_from.username.data)
            errors.update({'username': text_error})
            data = json.dumps(errors, ensure_ascii=True)
            return jsonify(data)
        current_user.create_family(user_partner)
        user_partner.create_family(current_user)
        db.session.commit()
        text_info = _('You are creating family with %(username)s!', username=user_partner.username)
        flash(text_info)
        return jsonify(status='ok')
    elif request.method == 'GET':
        search_from.username.data = ''
    else:
        data = json.dumps(search_from.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_modal_search_user.html', title=_('Search User'), form=search_from)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        if request.form.get('is_send_email') is not None:
            current_user.is_send_email = 't'
        else:
            current_user.is_send_email = 'f'
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.email.data = current_user.email
        if current_user.is_send_email == 't':
            form.is_send_email.data = 'y'
        else:
            form.is_send_email.data = None
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_form_edit.html', title=_('Edit Profile'), form=form)

@app.route('/family', methods=['GET'])
@login_required
def family():
    return render_template('family.html', title=_('Family'))

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = EmptyForm()
    status = get_status()
    type_user = None
    if request.method == "POST":
        type_user = request.form.get('type_user')

    user_partner = current_user.get_partner(current_user)
    user_partner_id = current_user.get_id_by_username(user_partner)

    if type_user == 'author':
        tasks_by_create_user = Tasks.query.filter_by(create_user=current_user.id)
        tasks = tasks_by_create_user.all()
    elif type_user == 'performer':
        tasks_by_id_users = Tasks.query.filter_by(id_users=current_user.id)
        tasks = tasks_by_id_users.all()
    else:
        tasks_by_create_user = Tasks.query.filter_by(create_user=current_user.id)
        tasks_by_id_users = Tasks.query.filter_by(id_users=current_user.id)

        tasks_by_partner_create_user = Tasks.query.filter_by(create_user=user_partner_id)
        tasks_by_partner_id_users = Tasks.query.filter_by(id_users=user_partner_id)

        tasks = tasks_by_create_user.union(tasks_by_id_users, tasks_by_partner_create_user, tasks_by_partner_id_users).order_by(Tasks.deadline.asc()).all()

    len_max = 0
    for i_status in range(0, len(status)): #проверяем в каком статусе задач больше всего для получения кол-ва строк в таблице
        if type_user == 'author':
            status_by_create_user = Tasks.query.filter_by(id_status=status[i_status]["id"], create_user=current_user.id)
            status_count = status_by_create_user.count()
        elif type_user == 'performer':
            status_by_id_users = Tasks.query.filter_by(id_status=status[i_status]["id"], id_users=current_user.id)
            status_count = status_by_id_users.count()
        else:
            status_by_create_user = Tasks.query.filter_by(id_status=status[i_status]["id"], create_user=current_user.id)
            status_by_id_users = Tasks.query.filter_by(id_status=status[i_status]["id"], id_users=current_user.id)

            status_by_partner_create_user = Tasks.query.filter_by(id_status=status[i_status]["id"], create_user=user_partner_id)
            status_by_partner_id_users = Tasks.query.filter_by(id_status=status[i_status]["id"], id_users=user_partner_id)

            status_count = status_by_create_user.union(status_by_id_users, status_by_partner_create_user, status_by_partner_id_users).count()
        if status_count > len_max:
            len_max = status_count

    #инициализация пустой таблицы с задачами для последующего заполнения
    list_tasks = [0] * len_max
    for i in range(0, len_max):
       list_tasks[i] = [0] * len(status)
    #переменные для подсчета кол-ва задач
    count_backlog = 0
    count_work = 0
    count_done = 0
    max_date_completion = None #переменная для самой ранней даты выполнения
    #заполнение таблицы с задачами
    for j in range(0, len(tasks)):
        for tr in range(0, len(list_tasks)):
            if list_tasks[tr][0] == 0 and tasks[j].id_status == 1:
                list_tasks[tr][0] = tasks[j]
                count_backlog = count_backlog + 1
                break
            if list_tasks[tr][1] == 0 and tasks[j].id_status == 2:
                list_tasks[tr][1] = tasks[j]
                count_work = count_work + 1
                break
            if list_tasks[tr][2] == 0 and tasks[j].id_status == 3:
                list_tasks[tr][2] = tasks[j]
                count_done = count_done + 1
                if max_date_completion is None:
                    max_date_completion = list_tasks[tr][2].date_completion
                else:
                    if list_tasks[tr][2].date_completion > max_date_completion:
                        max_date_completion = list_tasks[tr][2].date_completion
                break

    arr_new = []
    for tr_item_task_done in range(0, len(list_tasks)):
        if list_tasks[tr_item_task_done][2] != 0:
            arr_new.append(list_tasks[tr_item_task_done][2].date_completion)

    arr_new.sort(reverse=True)
    for item_sort in range(0, len(arr_new)):
        for item_task in range(0, len(list_tasks)):

            if list_tasks[item_task][2] != 0:
                if arr_new[item_sort] == list_tasks[item_task][2].date_completion:
                    temp_task = list_tasks[item_sort][2]
                    list_tasks[item_sort][2] = list_tasks[item_task][2]
                    list_tasks[item_task][2] = temp_task

    count_dict = {
        'count_backlog': count_backlog,
        'count_work': count_work,
        'count_done': count_done
    }

    return render_template('tasks.html', title=_('Tasks'), form=form, status=status, tasks=list_tasks,
                           count_tasks=count_dict)
@app.route('/tasks_by_user/<type_user>', methods=['GET'])
@login_required
def tasks_by_user(type_user):
    form = EmptyForm()
    status = get_status()

    if type_user == 'author':
        tasks_by_create_user = Tasks.query.filter_by(create_user=current_user.id)
        tasks = tasks_by_create_user.all()
    elif type_user == 'performer':
        tasks_by_id_users = Tasks.query.filter_by(id_users=current_user.id)
        tasks = tasks_by_id_users.all()

    len_max = 0
    for i_status in range(0, len(status)):#проверяем в каком статусе задач больше всего для получения кол-ва строк в таблице
        if type_user == 'author':
            status_by_create_user = Tasks.query.filter_by(id_status=status[i_status]["id"], create_user=current_user.id)
            status_count = status_by_create_user.count()
        elif type_user == 'performer':
            status_by_id_users = Tasks.query.filter_by(id_status=status[i_status]["id"], id_users=current_user.id)
            status_count = status_by_id_users.count()

        if status_count > len_max:
            len_max = status_count

    # инициализация пустой таблицы с задачами для последующего заполнения
    list_tasks = [0] * len_max
    for i in range(0, len_max):
        list_tasks[i] = [0] * len(status)
    # переменные для подсчета кол-ва задач
    count_backlog = 0
    count_work = 0
    count_done = 0
    # заполнение таблицы с задачами
    for j in range(0, len(tasks)):
        for tr in range(0, len(list_tasks)):
            if list_tasks[tr][0] == 0 and tasks[j].id_status == 1:
                list_tasks[tr][0] = tasks[j]
                count_backlog = count_backlog + 1
                break
            if list_tasks[tr][1] == 0 and tasks[j].id_status == 2:
                list_tasks[tr][1] = tasks[j]
                count_work = count_work + 1
                break
            if list_tasks[tr][2] == 0 and tasks[j].id_status == 3:
                list_tasks[tr][2] = tasks[j]
                count_done = count_done + 1
                break

    count_dict = {
        'count_backlog': count_backlog,
        'count_work': count_work,
        'count_done': count_done
    }
    return json.dumps({"data": render_template('tasks.html', title=_('Tasks'), form=form, status=status,
                                               tasks=list_tasks, count_tasks=count_dict)})

#функция для получения всех доступных видов задач
def get_type_task():
    type_task = TypeTask.query.all()
    list_type_task = []
    for t in type_task:
        type_task_dict = {"id": t.id, "name": t.name}
        list_type_task.append(type_task_dict)
    return list_type_task

#фукнция для получения всех доступных приоритетов
def get_priotity():
    priority = Priority.query.all()
    list_priority = []
    for p in priority:
        priority_dict = {"id": p.id, "name": p.name}
        list_priority.append(priority_dict)
    return list_priority

#функция для получения всех доступных статусов
def get_status():
    status = Status.query.all()
    list_status = []
    for s in status:
        status_dict = {"id": s.id, "name": s.name}
        list_status.append(status_dict)
    return list_status

#функция для получения всех доступных сложностей
def get_complexity():
    complexity = Complexity.query.all()
    list_complexity = []
    for c in complexity:
        complexity_dict = {"id": c.id, "name": c.name}
        list_complexity.append(complexity_dict)
    return list_complexity

#функция для получения всех доступных категорий
def get_category():
    category = Category.query.all()
    list_category = []
    for cat in category:
        category_dict = {"id": cat.id, "name": cat.name}
        list_category.append(category_dict)
    return list_category

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = AddTaskForm()
    type_task = get_type_task()
    priority = get_priotity()
    status = get_status()
    complexity = get_complexity()
    category = get_category()

    if form.validate_on_submit():
       if form.type_task.data == 3:
           if form.period_count.data is not None:
               task = Tasks(id_type_task=form.type_task.data, title=form.title.data, id_priority=form.priority.data,
                        id_status=status[0]["id"], deadline=form.deadline.data, description=form.description.data,
                        create_user=current_user.id, create_date=datetime.today(), date_completion=datetime.utcnow(),
                        id_complexity=form.complexity.data, id_category=form.category.data, period=form.period_count.data,
                        period_type=form.period_time.data)
       else:
           task = Tasks(id_type_task=form.type_task.data, title=form.title.data, id_priority=form.priority.data,
                        id_status=status[0]["id"], deadline=form.deadline.data, description=form.description.data,
                        create_user=current_user.id, create_date=datetime.utcnow(), date_completion=datetime.utcnow(),
                        id_complexity=form.complexity.data, id_category=form.category.data)
       db.session.add(task)
       db.session.commit()
       #созданием оповещения для задачи
       notify_obj = NotifySend(task.id, current_user)
       notify_obj.add_notify()
       flash(_('Task success added.'))
       return jsonify(status='ok', title_task=form.title.data)
    elif request.method == 'GET':
        form.deadline.data = datetime.now()
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_add_task.html', title=_('Add Task'), form=form, typies_task=type_task, priorities=priority, complexities=complexity, categories=category)

@app.route('/add_subtask/<task_id>', methods=['GET', 'POST'])
@login_required
def add_subtask(task_id):
    form = AddTaskForm()
    type_task = get_type_task()
    priority = get_priotity()
    status = get_status()
    complexity = get_complexity()
    category = get_category()

    if form.validate_on_submit():
       subtask = Tasks(id_type_task=2, title=form.title.data, id_priority=form.priority.data,
                    id_status=status[0]["id"], deadline=form.deadline.data, description=form.description.data,
                    create_user=current_user.id, create_date=datetime.utcnow(), date_completion=datetime.utcnow(),
                    id_complexity=form.complexity.data, id_category=form.category.data)
       db.session.add(subtask)
       current_task = Tasks.query.filter_by(id=task_id).first()
       current_task.create_subtask(subtask)
       db.session.commit()
       notify_obj = NotifySend(subtask.id, current_user)
       notify_obj.add_notify()
       flash(_('Subtask success added.'))
       return jsonify(status='ok', title_task=form.title.data)
    elif request.method == 'GET':
        form.deadline.data = datetime.now()
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_add_task.html', title=_('Add Subtask'), form=form, typies_task=type_task, priorities=priority, complexities=complexity, categories=category, task_id=task_id)

@app.route('/check_task', methods=['POST'])
@login_required
def check_task():
    task_id = request.json.get('id_task', None)
    task = Tasks.query.filter_by(id=task_id).first()
    status = Status.query.filter_by(id=task.id_status).first()
    answer = {
        "status": status.name,
        "type": task.id_type_task
    }
    return make_response(answer)

@app.route('/next_status', methods=['POST'])
@login_required
def next_status():
    status = get_status()
    task_id = request.json.get('id_task', None)
    task = Tasks.query.filter_by(id=task_id).first()
    old_id_status = task.id_status
    task.id_status = task.id_status + 1
    if old_id_status == 1 and task.id_status == 2 and task.id_users is None: #заполняем исполнителя, если перевели в работу и исполнитель еще не указан
        task.id_users = current_user.id
    elif old_id_status == 2 and task.id_status == 3:
        task.date_completion = datetime.utcnow()
        #если перевели задачу в статус "Готово", то удаляем оповещения
        notify_obj = NotifySend(task.id, current_user)
        notify_obj.delete_notify()
        if task.id_type_task == 3:
            duplicate_task(task, status)
    db.session.commit()
    flash(_('Task %(title)s success update', title=task.title))
    status_name = ""
    for s in range(0, len(status), 1):
        if status[s]["id"] == task.id_status:
            status_name = status[s]["name"]

    soup = BeautifulSoup(tasks(), 'html.parser')
    response_answer = {
        'title_task': task.title,
        'status_name': status_name,
        'html_tasks': str(soup.select_one('.table-responsive'))
    }
    return make_response(response_answer)

@app.route('/previous_status', methods=['POST'])
@login_required
def previous_status():
    task_id = request.json.get('id_task', None)
    task = Tasks.query.filter_by(id=task_id).first()
    old_id_status = task.id_status
    task.id_status = task.id_status - 1
    if old_id_status == 3 and task.id_status == 2:
        task.date_completion = None
        #если вернули задачу из статуса готово, то создаем оповещения
        notify_obj = NotifySend(task.id, current_user)
        notify_obj.add_notify()
    db.session.commit()
    flash(_('Task %(title)s success update', title=task.title))
    status = get_status()
    status_name = ""
    for s in range(0, len(status), 1):
        if status[s]["id"] == task.id_status:
            status_name = status[s]["name"]

    soup = BeautifulSoup(tasks(), 'html.parser')
    response_answer = {
        'title_task': task.title,
        'status_name': status_name,
        'html_tasks': str(soup.select_one('.table-responsive'))
    }
    return make_response(response_answer)


@app.route('/edit_task/<id_task>', methods=['GET', 'POST'])
@login_required
def edit_task(id_task):
    task = Tasks.query.filter_by(id=id_task).first()
    if task is not None:
        type_task = get_type_task()
        priority = get_priotity()
        complexity = get_complexity()
        status = get_status()
        category = get_category()
        form = ShowTaskForm()

        if request.method == 'GET':
            # заполнение исполнителя
            if task.id_users is not None:
                form.user.data = current_user.get_user(task.id_users)

            #отображение статуса по задаче
            for s in range(0, len(status)):
                if status[s]["id"] == task.id_status:
                    form.status.data = status[s]["name"]

            form.title.data = task.title
            if task.id_type_task == 3:
                form.period_count.data = task.period
                form.period_time.data = task.period_type
            form.description.data = task.description
            form.deadline.data = task.deadline

            return render_template('show_task.html', title=_('Task'), form=form, task=task, priorities=priority,
                                   complexities=complexity, categories=category, typies=type_task)

        elif request.method == 'POST':
            if form.validate_on_submit():
                task.title = form.title.data
                task.id_type_task = form.type_task.data
                task.description = form.description.data
                if form.user.data is not None and form.user.data != "":
                    task.id_users = current_user.get_id_by_username(form.user.data)
                else:
                    task.id_users = None

                task.id_priority = form.priority.data
                if (task.deadline.strftime('%Y-%m-%d')) != form.deadline.data.strftime('%Y-%m-%d'):
                    task.deadline_25_percent = None
                    task.deadline_50_percent = None
                    task.deadline_75_percent = None
                    task.deadline_100_percent = None
                    #обновляем время отправки оповещений
                    notify_obj = NotifySend(task.id, current_user)
                    notify_obj.update_notify()

                task.deadline = form.deadline.data
                task.id_complexity = form.complexity.data
                task.id_category = form.category.data
                if int(task.id_type_task) == 3:
                    task.period = form.period_count.data
                    task.period_type = form.period_time.data
                db.session.commit()
                flash(_('Task %(title)s success update', title=task.title))
            else:
                flash('Error validation update task')
            return render_template('show_task.html', title=_('Task'), form=form, task=task, priorities=priority,
                                   complexities=complexity, categories=category, typies=type_task)

    return redirect(url_for('tasks'))


@app.route('/save_notify', methods=['POST'])
@login_required
def save_notify():
    sub_user = str(request.get_json())
    print('sub_user', sub_user)
    subscriprion = Subscription.query.filter_by(id_users=current_user.id, push_param=sub_user).first()
    if subscriprion is None:
        if sub_user is None:
            subscription = Subscription(id_users=current_user.id, push_param=current_user.email)
        else:
            subscription = Subscription(id_users=current_user.id, push_param=sub_user)
        db.session.add(subscription)
        db.session.commit()
    return make_response('success')

@app.route('/send_push', methods=['POST'])
@login_required
def send_push_notification():
    data = json.dumps(request.get_json())
    data_param = json.loads(data)
    data_push = json.dumps({
        "title": data_param["title"],
        "body": data_param["body"]
    })

    print('data param', data_param)
    if data_param["param"] is not None:
        data_param_push_json_endpoint = json.loads(data_param["param"])["endpoint"]
    else:
        data_param_push_json_endpoint = ""

    user_partner = current_user.get_partner(current_user)
    partner_user = Users.query.filter_by(username=user_partner).first()
    partner_email = partner_user.email
    print('partner_email', partner_email)
    user_subscription = Subscription.query.filter_by(id_users=partner_user.id).all()

    for subscr in range(0, len(user_subscription)):#отправка оповещений по на подписанный устройства и браузеры партнера
        print('user_subscription[subscr].push_param', user_subscription[subscr].push_param)
        if user_subscription[subscr].push_param != partner_email:
            push_param = json.loads((user_subscription[subscr].push_param).replace('\'', '\"').replace("None", "\"\""))
            print('user id', user_subscription[subscr].id_users)
            print('push_param endpoint', push_param['endpoint'])
            if (data_param_push_json_endpoint != push_param['endpoint']): #не отправляем оповещение в браузер в котором произошло действие
                print('send webpush')
                try:
                    webpush(
                        subscription_info=push_param,
                        data=data_push,
                        vapid_private_key='./private_key.pem',
                        vapid_claims={
                            'sub': 'mailto:{}'.format(app.config['ADMINS'][0])
                        }
                    )
                    flag_send_push = True
                except WebPushException as ex:
                    print('I can\'t do that: {}'.format(repr(ex)))
                    print(ex)
                    if ex.response.status_code == 410:
                        print('subscr 410 error', user_subscription[subscr].id_users, user_subscription[subscr].push_param)
                        db.session.delete(user_subscription[subscr])
                        db.session.commit()
                    # Mozilla returns additional information in the body of the response.
                    if ex.response and ex.response.json():
                        extra = ex.response.json()
                        print('Remote service replied with a {}:{}, {}',
                              extra.code,
                              extra.errno,
                              extra.message)

    #дублирование оповещения на почту партнера
    if partner_user.is_send_email != 'f':
        print('send email notify')
        send_email(data_param["title"],
                   sender=app.config['ADMINS'][0],
                   recipients=[partner_email],
                   text_body=data_param["body"],
                   html_body=""
                   )

    response_answer = {
        'response': 'Send notify success',
    }
    return make_response(response_answer)

@app.route('/reset_password_request', methods = ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title=_('Reset Password'), form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if (form.photo.data.filename.find(' ') > 0):
                filename_str = form.photo.data.filename.split()
                filename_photo = '_'.join(filename_str)
            else:
                filename_photo = form.photo.data.filename
            if not os.path.isdir(app.config['UPLOADED_PHOTOS_DEST']):
                os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
            path = app.config['FOLDER_NAME_IMG'] + "/" + filename_photo
            user = Users.query.filter_by(username=current_user.username, url_photo=path).first()
            if user is None:
                photos.save(form.photo.data)#обновляем фото профиля
                current_user.set_photo(path)
                db.session.commit()
                flash(_('Your photo has been update.'))
                return jsonify(status='ok')
            else:
                errors = {"photo.exists": _("This photo is exists.")}
                data = json.dumps(errors, ensure_ascii=True)
                return jsonify(data)
        else:
            data = json.dumps(form.errors, ensure_ascii=True)
            return jsonify(data)
    return render_template("_modal_upload_file.html", form=form, title=_('Edit Photo'))

def duplicate_task(task, status):
    if task.period_type == "Days":
        delta = timedelta(days=task.period)
        deadline_time = task.date_completion + delta
    elif task.period_type == "Weeks":
        delta = timedelta(weeks=task.period)
        deadline_time = task.date_completion + delta
    elif task.period_type == "Months":
        deadline_time = task.date_completion + relativedelta(months=+task.period)
    elif task.period_type == "Years":
        deadline_time = task.date_completion + relativedelta(years=+task.period)
    task = Tasks(id_type_task=task.id_type_task, title=task.title, id_priority=task.id_priority,
                 id_status=status[0]["id"], deadline=deadline_time, description=task.description,
                 create_user=current_user.id, create_date=datetime.utcnow(), id_complexity=task.id_complexity,
                 id_category=task.id_category, period=task.period, period_type=task.period_type)
    db.session.add(task)
    db.session.commit()
    notify_obj = NotifySend(task.id, current_user)
    notify_obj.add_notify()
    flash(_('Task success added.'))

@app.route('/delete_task', methods=['GET', 'POST'])
@login_required
def delete_task():
    # сначала удаляем оповещения, а потом задачу
    if request.json.get('id_task', None) is not None:
        notify_obj = NotifySend(request.json.get('id_task', None), current_user)
        notify_obj.delete_notify()

    task = Tasks.query.filter_by(id=request.json.get('id_task', None)).first()
    if task is not None:
        db.session.delete(task)
        flash(_('Task %(title)s success delete', title=task.title))
        db.session.commit()

    soup = BeautifulSoup(tasks(), 'html.parser')
    response_answer = {
        'title_task': task.title,
        'html_tasks': str(soup.select_one('.table-responsive'))
    }
    return make_response(response_answer)

@app.route('/check_subtask', methods=['POST'])
@login_required
def check_subtask():
    task = Tasks.query.filter_by(id=request.json.get('id_task', None)).first()
    if task.is_subtask(task):
        return make_response("true")
    else:
        return make_response("false")

@scheduler.task(
    "interval",
    id="job_sync",
    seconds=60,
    max_instances=1,
    start_date="2023-01-01 00:00:00",
)
def send_push_notification_by_normativ():
    with scheduler.app.app_context():
        tasks = Tasks.query.filter(Tasks.id_status != 3).all()
        if tasks is not None:
            for task in tasks:
                notify_obj = NotifySend(task.id, current_user)
                notify_obj.send_webpush_notify()
                notify_obj.send_email_notify()