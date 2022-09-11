import datetime
import json
from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from app import app, db, photos
from app.forms import LoginForm, RegistrationForm, SearchUserForm, EditProfileForm, AddTaskForm, \
    EmptyForm, ShowTaskForm, ResetPasswordRequestForm, ResetPasswordForm, UploadForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users, TypeTask, Priority, Status, Tasks, Complexity, Subscription, Category
from werkzeug.urls import url_parse
from datetime import datetime
from pywebpush import webpush, WebPushException
from app.email import send_password_reset_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

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
        if user_partner.is_family(user_partner) > 0:
            errors.update({'username': 'User {} have family!'.format(search_from.username.data)})
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

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = EmptyForm()
    status = get_status()
    type_user = None
    if request.method == "POST":
        type_user = request.form['type_user']
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
    for i_status in range(0, len(status)):  # проверяем в каком статусе задач больше всего для получения кол-ва строк в таблице
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
        tasks[j].create_date = tasks[j].create_date.strftime('%d.%m.%y %H:%M')  # преобразование даты
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
    return json.dumps({"data": render_template('tasks.html', title='Tasks', form=form, status=status, tasks=list_tasks,
                           count_tasks=count_dict)})

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

       if form.type_task.data is None:
           form.type_task.data = 1

       task = Tasks(id_type_task=type_task[0]["id"], title=form.title.data, id_priority=form.priority.data,
                    id_status=status[0]["id"], deadline=form.deadline.data, description=form.description.data,
                    create_user=current_user.id, create_date=datetime.today().strftime("%d-%m-%Y %H:%M:%S"),
                    id_complexity=form.complexity.data, id_category=form.category.data)
       db.session.add(task)
       db.session.commit()
       flash('Task success added.')
       return jsonify(status='ok', title_task=form.title.data)
    elif request.method == 'GET':
        form.deadline.data = datetime.now()
    else:
        data = json.dumps(form.errors, ensure_ascii=True)
        return jsonify(data)
    return render_template('_add_task.html', title='Add Task', form=form, typies_task=type_task, priorities=priority, complexities=complexity, categories=category)

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
    if old_id_status == 1 and task.id_status == 2 and task.id_users is None: #заполняем исполнителя, если перевели в работу и исполнитель еще не указан
        task.id_users = current_user.id
    elif old_id_status == 2 and task.id_status == 3:
        task.date_completion = datetime.today()
    db.session.commit()
    flash('Task {} success update'.format(task.title))
    status = get_status()
    status_name = ""
    for s in range(0, len(status), 1):
        if status[s]["id"] == task.id_status:
            status_name = status[s]["name"]
    response_answer = {
        'title_task': task.title,
        'status_name': status_name
    }
    return make_response(response_answer)

@app.route('/previous_status', methods=['POST'])
@login_required
def previous_status():
    task_id = request.form['id_task']
    task = Tasks.query.filter_by(id=task_id).first()
    old_id_status = task.id_status
    task.id_status = task.id_status - 1
    if old_id_status == 3 and task.id_status == 2:
        task.date_completion = None
    db.session.commit()
    flash('Task {} success update'.format(task.title))
    status = get_status()
    status_name = ""
    for s in range(0, len(status), 1):
        if status[s]["id"] == task.id_status:
            status_name = status[s]["name"]
    response_answer = {
        'title_task': task.title,
        'status_name': status_name
    }
    return make_response(response_answer)


@app.route('/edit_task/<id_task>', methods=['GET', 'POST'])
@login_required
def edit_task(id_task):
    task = Tasks.query.filter_by(id=id_task).first()
    if task is not None:
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
            form.description.data = task.description
            form.deadline.data = task.deadline

            if task.date_completion is not None:
                task.date_completion = task.date_completion.strftime('%d.%m.%y %H:%M')  # преобразование даты

            return render_template('show_task.html', title='Task', form=form, task=task, priorities=priority, complexities=complexity, categories=category)

        elif request.method == 'POST':
            if form.validate_on_submit():
                task.title = form.title.data
                task.description = form.description.data

                if form.user.data is not None and form.user.data != "":
                    task.id_users = current_user.get_id_by_username(form.user.data)

                task.id_priority = form.priority.data
                task.deadline = form.deadline.data
                task.id_complexity = form.complexity.data
                task.id_category = form.category.data
                db.session.commit()
                flash('Task {} success update'.format(task.title))
            return render_template('show_task.html', title='Task', form=form, task=task, priorities=priority, complexities=complexity, categories=category)

    return redirect(url_for('tasks'))


@app.route('/save_notify', methods=['POST'])
@login_required
def save_notify():
    sub_user = str(request.get_json())
    subscriprion = Subscription.query.filter_by(id_users=current_user.id, push_param=sub_user).first()
    if subscriprion is None:
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
    data_param_push_json_endpoint = json.loads(data_param["param"])["endpoint"]
    id_user_partner = current_user.get_id_by_username(current_user.get_partner(current_user))
    user_subscription = Subscription.query.filter_by(id_users=id_user_partner).all()
    for subscr in range(0, len(user_subscription)):
        push_param = json.loads((user_subscription[subscr].push_param).replace('\'', '\"').replace("None", "\"\""))
        if (data_param_push_json_endpoint != push_param['endpoint']): #не отправляем оповещение в браузер в котором произошло действие
            try:
                webpush(
                    subscription_info=push_param,
                    data=data_push,
                    vapid_private_key='./private_key.pem',
                    vapid_claims={
                        'sub': 'mailto:{}'.format(app.config['ADMINS'][0])
                    }
                )
            except WebPushException as ex:
                print('I can\'t do that: {}'.format(repr(ex)))
                print(ex)
                # Mozilla returns additional information in the body of the response.
                if ex.response and ex.response.json():
                    extra = ex.response.json()
                    print('Remote service replied with a {}:{}, {}',
                          extra.code,
                          extra.errno,
                          extra.message)

    return make_response('success')

@app.route('/reset_password_request', methods = ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

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
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            path = app.config['FOLDER_NAME_IMG'] + "/" + form.photo.data.filename
            user = Users.query.filter_by(username=current_user.username, url_photo=path).first()
            if user is None:
                photos.save(form.photo.data)#обновляем фото профиля
                current_user.set_photo(path)
                db.session.commit()
                flash('Your photo has been update.')
                return jsonify(status='ok')
            else:
                errors = {"photo.exists": "This photo is exists."}
                data = json.dumps(errors, ensure_ascii=True)
                return jsonify(data)
        else:
            data = json.dumps(form.errors, ensure_ascii=True)
            return jsonify(data)
    return render_template("_modal_upload_file.html", form=form, title='Edit Photo')