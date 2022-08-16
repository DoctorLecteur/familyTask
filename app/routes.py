import datetime
import json
from flask import render_template, flash, redirect, url_for, request, jsonify, make_response, session
from app import app, db
from app.forms import LoginForm, RegistrationForm, SearchUserForm, EditProfileForm, AddTaskForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users, TypeTask, Priority, Status, Tasks
from werkzeug.urls import url_parse
from datetime import datetime
from sqlalchemy import select, or_, text

@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.is_authenticated and current_user.is_family(current_user):
        return redirect(url_for('tasks'))
    elif current_user.is_authenticated and not current_user.is_family(current_user):
        return redirect(url_for('user', username=current_user.username))
    return render_template('index.html', title='Home Page')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

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
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

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
            errors.update({'username': 'User {} not found. Repeat search.'.format(search_from.username.data)})
            data = json.dumps(errors, ensure_ascii=True)
            return jsonify(data)
        if user_partner == current_user:
            errors.update({'username': 'You cannot create family only yourself!'})
            data = json.dumps(errors, ensure_ascii=True)
            return jsonify(data)
        current_user.create_family(user_partner)
        user_partner.create_family(current_user)
        db.session.commit()
        flash('You are creating family with {}!'.format(user_partner.username))
        return jsonify(status='ok')
    elif request.method == 'GET':
        search_from.username.data = ''
    else:
        data = json.dumps(search_from.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_modal_search_user.html', title='Search User', form=search_from)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Your changes have been saved.')
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.email.data = current_user.email
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_form_edit.html', title='Edit Profile', form=form)

@app.route('/family', methods=['GET'])
@login_required
def family():
    return render_template('family.html', title='Family')

@app.route('/tasks', methods=['GET'])
@login_required
def tasks():
    form = EmptyForm()
    status = get_status()
    tasks_by_create_user = Tasks.query.filter_by(create_user=current_user.id)
    tasks_by_id_users = Tasks.query.filter_by(id_users=current_user.id)
    tasks = tasks_by_create_user.union(tasks_by_id_users).order_by(Tasks.deadline.asc()).all()

    len_max = 0
    for i_status in range(0, len(status)): #проверяем в каком статусе задач больше всего для получения кол-ва строк в таблице
        status_by_create_user = Tasks.query.filter_by(id_status=status[i_status]["id"], create_user=current_user.id)
        status_by_id_users = Tasks.query.filter_by(id_status=status[i_status]["id"], id_users=current_user.id)
        status_count = status_by_create_user.union(status_by_id_users).count()
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
    #заполнение таблицы с задачами
    for j in range(0, len(tasks)):
        tasks[j].create_date = tasks[j].create_date.strftime('%d.%m.%y %H:%M') #преобразование даты
        tasks[j].deadline = tasks[j].deadline.strftime('%d.%m.%y')  # преобразование даты
        if tasks[j].date_completion is not None:
            tasks[j].date_completion = tasks[j].date_completion.strftime('%d.%m.%y %H:%M')  # преобразование даты
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
    return render_template('tasks.html', title='Tasks', form=form, status=status, tasks=list_tasks, count_tasks=count_dict)

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

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = AddTaskForm()
    type_task = get_type_task()
    priority = get_priotity()
    status = get_status()
    if form.validate_on_submit():

       if form.type_task.data is None:
           form.type_task.data = 1

       task = Tasks(id_type_task=type_task[0]["id"], title=form.title.data, id_priority=form.priority.data,
                    id_status=status[0]["id"], deadline=form.deadline.data, description=form.description.data,
                    create_user=current_user.id, create_date=datetime.today().strftime("%d-%m-%Y %H:%M:%S"))
       db.session.add(task)
       db.session.commit()
       flash('Task success added.')
       return jsonify(status='ok')
    elif request.method == 'GET':
        form.deadline.data = datetime.now()
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_add_task.html', title='Add Task', form=form, typies_task=type_task, priorities=priority)

@app.route('/check_task', methods=['POST'])
@login_required
def check_task():
    task_id = request.form['id_task']
    task = Tasks.query.filter_by(id=task_id).first()
    status = Status.query.filter_by(id=task.id_status).first()
    return make_response(status.name)

@app.route('/next_status', methods=['POST'])
@login_required
def next_status():
    task_id = request.form['id_task']
    task = Tasks.query.filter_by(id=task_id).first()
    old_id_status = task.id_status
    task.id_status = task.id_status + 1
    if old_id_status == 1 and task.id_status == 2: #заполняем исполнителя, если перевели в работу
        task.id_users = current_user.id
    elif old_id_status == 2 and task.id_status == 3:
        task.date_completion = datetime.today()
    db.session.commit()
    flash('Task {} success update'.format(task.title))
    return make_response('success')