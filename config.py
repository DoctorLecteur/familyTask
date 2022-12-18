import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you_will-family-task'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
                              ''test''
                            # ''test''

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NOTIFICATION_KEY = ''test''
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or ''test''
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or 1
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''test''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''test''
    ADMINS = [''test'']
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    UPLOADED_PHOTOS_DEST = "app/static/img"
    FOLDER_NAME_IMG = "/static/img"
    LANGUAGES = ['en', 'ru']
