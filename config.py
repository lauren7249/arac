import os


class Config(object):
    SECRET_KEY = os.getenv('PRIME_SECRET_KEY', 'jfiesjof3920uf90esc09w3fj903w3')
    CSRF_SESSION_KEY = "iejfjenosvfse87r3729rfu8ej"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    ASSETS_DEBUG = False
    MAIL_SUPPRESS_SEND = True
    COOKIE_SECURE = False

    MAIL_SERVER = 'aws_string_goes_here'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    # Flask-Login
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    AWS_ACCESS_KEY_ID='AKIAIWG5K3XHEMEN3MNA'
    AWS_SECRET_ACCESS_KEY='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'
    STATIC_URL = "/static/"
    SENDGRID_EMAIL = "lauren7249"
    SENDGRID_PASSWORD = "1250downllc"
    SENDGRID_FROM_EMAIL = "contacts@advisorconnect.co"


class BetaConfig(Config):
#    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@babel/arachnid'
    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@10.143.114.188/arachnid' 
    BASE_URL = 'https://prime.advisorconnect.co'


class DevelopmentConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost:5432/arachnid'
    ASSETS_DEBUG = False
    MAIL_SUPPRESS_SEND = True
    COOKIE_SECURE = False
    BASE_URL = 'https://beta.advisorconnect.co'
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@arachnid.cc540uqgo1bi.us-east-1.rds.amazonaws.com:5432/arachnid'
    BASE_URL = 'https://prime.advisorconnect.co'


class TestingConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URL','postgresql://localhost:5432/arachnid')
    ASSETS_DEBUG = False
    MAIL_SUPPRESS_SEND = True
    COOKIE_SECURE = False
    BASE_URL = 'http://localhost:5000'



config = {
    'development': DevelopmentConfig,
    'beta': BetaConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
