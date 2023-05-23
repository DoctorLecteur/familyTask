from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_babel import Babel
import logging
from logging.handlers import SMTPHandler
from flask_babel import _, lazy_gettext as _l
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_babel import _, lazy_gettext as _l
import os
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = _l('Please log in to access this page.')
bootstrap = Bootstrap(app)
mail = Mail(app)
moment = Moment(app)
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
babel = Babel(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_SERVER'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['ADMINS'],
            toaddrs=app.config['ADMINS'], subject='FamilyTask Failure',
            credentials=auth, secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('FamilyTask startup')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from app import routes, models, errors