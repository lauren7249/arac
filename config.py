import os


class Config(object):
    SECRET_KEY = os.getenv('PRIME_SECRET_KEY', 'jfiesjof3920uf90esc09w3fj903w3')

    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    MAIL_SERVER = 'aws_string_goes_here'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    # Flask-Login
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


class BetaConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@arachnid.cc540uqgo1bi.us-east-1.rds.amazonaws.com:5432/arachnid'
    #ARACHNID_SERVER_URL = 'http://prime.advisorconnect.co'


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@localhost:5432/arachnid'
    ASSETS_DEBUG = True
    MAIL_SUPPRESS_SEND = True
    COOKIE_SECURE = False
    ARACHNID_SERVER_URL = 'http://localhost:5000'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://acprime:acprime101B@localhost:5432/acprime'



config = {
    'development': DevelopmentConfig,
    'beta': BetaConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig
}
