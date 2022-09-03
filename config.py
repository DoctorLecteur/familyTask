import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you_will-family-task'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
                              ''test''
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NOTIFICATION_KEY = ''test''