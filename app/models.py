from app import db, login, app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt

family = db.Table('family',
                  db.Column('id_user', db.Integer, db.ForeignKey('users.id')),
                  db.Column('id_partner', db.Integer, db.ForeignKey('users.id'))
                )

subtasks = db.Table('subtasks',
                    db.Column('id_task', db.Integer, db.ForeignKey('tasks.id')),
                    db.Column('id_subtask', db.Integer, db.ForeignKey('tasks.id'))
                    )

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    url_photo = db.Column(db.String(512))
    is_send_email = db.Column(db.String(1), default=False)

    families = db.relationship(
        'Users', secondary=family,
        primaryjoin=(family.c.id_user == id),
        secondaryjoin=(family.c.id_partner == id),
        backref=db.backref('family', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def create_family(self, user):
        if not self.is_family(user):
            self.families.append(user)

    def destroy_family(self, user):
        if self.is_family(user):
            self.families.remove(user)

    def is_family(self, user):
        return self.families.filter(
            family.c.id_user == user.id).count() > 0

    def get_partner(self, user):
        return self.families.filter(
            family.c.id_user == user.id).first_or_404().username

    def get_user(self, id):
        return self.query.filter_by(id=id).first_or_404().username

    def get_last_seen_by_username(self, username):
        return self.query.filter_by(username=username).first_or_404().last_seen

    def get_id_by_username(self, username):
        return self.query.filter_by(username=username).first_or_404().id

    def get_email_by_username(self, username):
        return self.query.filter_by(username=username).first_or_404().email

    def get_id_partner_by_id_user(self, id):
        return self.families.filter(family.c.id_user == id).first_or_404().id

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Users.query.get(id)

    def get_photo_by_username(self, username):
        return self.query.filter_by(username=username).first_or_404().url_photo

    def set_photo(self, url_photo):
        self.url_photo = url_photo

@login.user_loader
def load_user(id):
    return Users.query.get(int(id))

class Priority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Priority {}>'.format(self.name)

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Status {}>'.format(self.name)

class TypeTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<TypeTask {}>'.format(self.name)


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    id_type_task = db.Column(db.Integer, db.ForeignKey('type_task.id'))
    title = db.Column(db.String(64), index=True)
    id_priority = db.Column(db.Integer, db.ForeignKey('priority.id'))
    id_status = db.Column(db.Integer, db.ForeignKey('status.id'), index=True)
    id_users = db.Column(db.Integer, db.ForeignKey('users.id'))
    deadline = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(1024))
    create_user = db.Column(db.Integer, db.ForeignKey('users.id'))
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    date_completion = db.Column(db.DateTime, default=datetime.utcnow)
    id_complexity = db.Column(db.Integer, db.ForeignKey('complexity.id'))
    id_category = db.Column(db.Integer, db.ForeignKey('category.id'))
    period = db.Column(db.Integer)
    period_type = db.Column(db.String(24))
    deadline_25_percent = db.Column(db.String(1))
    deadline_50_percent = db.Column(db.String(1))
    deadline_75_percent = db.Column(db.String(1))
    deadline_100_percent = db.Column(db.String(1))

    subtask =  db.relationship(
        'Tasks', secondary=subtasks,
        primaryjoin=(subtasks.c.id_task == id),
        secondaryjoin=(subtasks.c.id_subtask == id),
        backref=db.backref('subtasks', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Tasks {}>'.format(self.title)

    def create_subtask(self, task):
        if not self.is_subtask(task):
            self.subtask.append(task)

    def is_subtask(self, task):
        return self.subtask.filter(
            subtasks.c.id_task == task.id).count() > 0

    def get_type_task(self, id_type_task):
        return TypeTask.query.filter_by(id=id_type_task).first_or_404().name

    def get_subtask_title(self, task):
        return self.subtask.filter(
            subtasks.c.id_task == task.id).first_or_404().title

    def get_subtask_id(self, task):
        return self.subtask.filter(
            subtasks.c.id_task == task.id).first_or_404().id

    def get_subtasks(self, task):
        return self.subtask.filter(
            subtasks.c.id_task == task.id).all()


class Complexity(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Complexity {}>'.format(self.name)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    id_users = db.Column(db.Integer, db.ForeignKey('users.id'))
    push_param = db.Column(db.String(1024))

    def __repr__(self):
        return '<Subscription {}>'.format(self.push_param)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(128), unique=True)

    def __repr__(self):
        return '<Category {}>'.format(self.name)

class Notify(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    type = db.Column(db.String(64))
    method = db.Column(db.String(64))
    time = db.Column(db.DateTime, default=datetime.utcnow)
    id_recipient = db.Column(db.Integer, db.ForeignKey('users.id'))
    id_task = db.Column(db.Integer, db.ForeignKey('tasks.id'))