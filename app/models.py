from app import db
from datetime import datetime

family = db.Table('family',
                  db.Column('id_user', db.Integer, db.ForeignKey('users.id')),
                  db.Column('id_partner', db.Integer, db.ForeignKey('users.id'))
                )

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Tasks', backref='author', lazy='dynamic')

    families = db.relationship(
        'Users', secondary=family,
        primaryjoin=(family.c.id_user == id),
        secondaryjoin=(family.c.id_partner == id),
        backref=db.backref('family', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

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
    id = db.Column(db.Integer, primary_key=True)
    id_type_task = db.Column(db.Integer, db.ForeignKey('type_task.id'))
    title = db.Column(db.String(64), index=True)
    id_priority = db.Column(db.Integer, db.ForeignKey('priority.id'))
    id_status = db.Column(db.Integer, db.ForeignKey('status.id'))
    id_users = db.Column(db.Integer, db.ForeignKey('users.id'))
    deadline = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(1024))

    def __repr__(self):
        return '<Tasks {}>'.format(self.title)