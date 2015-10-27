import os


class Config(object):
    SECRET_KEY = os.getenv('PRIME_SECRET_KEY', 'jfiesjof3920uf90esc09w3fj903w3')
    CSRF_SESSION_KEY = "iejfjenosvfse87r3729rfu8ej"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    ASSETS_DEBUG = True
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
    #REDSHIFT_DATABASE_URI = 'postgresql://acprime:acprime101B@localhost:5432/acprime'
    SQLALCHEMY_DATABASE_URI = 'postgresql://arachnid:devious8ob8@arachnid.cc540uqgo1bi.us-east-1.rds.amazonaws.com:5432/arachnid'


class NYLConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://nyl:newyorklife@localhost:5432/nyl'
    ASSETS_DEBUG = True
    MAIL_SUPPRESS_SEND = True
    COOKIE_SECURE = False
    SERVER_URL = 'http://localhost:5000'



config = {
    'development': DevelopmentConfig,
    'beta': BetaConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig,
    'nyl': NYLConfig
}
