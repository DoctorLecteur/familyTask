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

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

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

    def __repr__(self):
        return '<Tasks {}>'.format(self.title)

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