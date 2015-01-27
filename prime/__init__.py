import logging
from logging.handlers import SysLogHandler

from flask import Flask
from flask.ext.assets import Environment
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from webassets import Bundle


from config import config


db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CsrfProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    log_format = ('%(asctime)s %(levelname)s: %(message)s '
                  '[%(pathname)s:%(lineno)d]')
    app.debug_log_format = log_format
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Using config: {}'.format(config_name))
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    #mail.init_app(app)
    init_assets(app)
    register_blueprints(app)

    return app


def init_assets(app):
    assets_environment = Environment(app)
    css = Bundle('css/bootswatch.min.css','css/main.css',
                 output='css/gen/main.%(version)s-fitzmin.css',
                 filters='cssmin')
    assets_environment.register('css_all', css)



def register_blueprints(app):
    from .prospects import prospects as prospects_blueprint
    from .proxy import proxy as proxy_blueprint
    from .users import users as users_blueprint
    from .auth import auth as auth_blueprint
    app.register_blueprint(prospects_blueprint)
    app.register_blueprint(proxy_blueprint)
    app.register_blueprint(users_blueprint)
    app.register_blueprint(auth_blueprint)


    #from .auth import auth as auth_blueprint
    #app.register_blueprint(auth_blueprint, url_prefix='/auth')
