import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')
import logging
from logging.handlers import SysLogHandler

from flask import Flask
from flask.ext.assets import Environment
from flask.ext.rq import RQ
from redis import Redis
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from webassets import Bundle
from flask.ext.admin import Admin
from flask_sslify import SSLify

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CsrfProtect()

def get_conn():
    from prime.processing_service.constants import REDIS_URL
    if os.getenv('AC_CONFIG') == 'beta':
        conn = Redis.from_url(url=REDIS_URL, db=0)
    elif os.getenv('REDIS_URL'):
        conn = Redis.from_url(url=os.getenv('REDIS_URL'), db=0)
    else:
        conn = Redis.from_url(url='redis://localhost:6379', db=0)
    return conn

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    log_format = ('%(asctime)s %(levelname)s: %(message)s '
                  '[%(pathname)s:%(lineno)d]')
    #app.debug_log_format = log_format
    #app.logger.setLevel(logging.DEBUG)
    app.logger.info('Using config: {}'.format(config_name))
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    #mail.init_app(app)
    init_assets(app)
    register_blueprints(app)
    #init_admin(app)
    add_template_globals(app)
    RQ(app)
    if config == 'beta':
        SSLify(app)
    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='https://97521d50b8d647d2b25d7a29f4895ce1:7cd28a9ea427402987b40b1a08b834de@app.getsentry.com/74764')
    return app

def init_assets(app):
    assets_environment = Environment(app)
    css = Bundle('css/chosen.css', 'css/hint.css', 'css/poppins.css', 'css/master.css',
                 output='css/gen/main.%(version)s-min.css',
                 filters='cssmin')
    assets_environment.register('css_all', css)


def register_blueprints(app):
    from .prospects import prospects as prospects_blueprint
    from .users import users as users_blueprint
    from .auth import auth as auth_blueprint
    from .managers import manager as manager_blueprint
    from .processing_service import processing_service as processing_service_blueprint
    from .crawlera import crawlera as crawlera_blueprint
    app.register_blueprint(prospects_blueprint)
    app.register_blueprint(users_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(processing_service_blueprint)
    app.register_blueprint(manager_blueprint, url_prefix='/managers')
    app.register_blueprint(crawlera_blueprint, url_prefix='/crawlera')


def add_template_globals(app):

    @app.template_global()
    def static_url():
        return app.config.get('STATIC_URL')

