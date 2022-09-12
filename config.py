import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you_will-family-task'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
                              ''test''
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NOTIFICATION_KEY = ''test''
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [''test'']
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    UPLOADED_PHOTOS_DEST = "app/static/img"
    FOLDER_NAME_IMG = "/static/img"
    LANGUAGES = ['en', 'ru']
