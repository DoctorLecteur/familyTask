import os
from dotenv import load_dotenv

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you_will-family-task'
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NOTIFICATION_KEY = os.getenv('NOTIFICATION_KEY')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    ADMINS = [''test'']
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    UPLOADED_PHOTOS_DEST = "app/static/photos"
    FOLDER_NAME_IMG = "/static/photos"
    LANGUAGES = ['en', 'ru']
