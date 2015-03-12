from prime.prospects.process_entity import * 
from prime.prospects import models
from prime.prospects.models import *
from prime import create_app
import os
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

@celery.task
def process_school_ids(items):
	try:
		capp = create_app(os.getenv('AC_CONFIG', 'beta'))
		db = SQLAlchemy(capp)
		session = db.session
	except:
		from prime import db
		session = db.session	
    
	
	for item in items:
		process_school(item, session)

@celery.task
def process_company_ids(items):
	try:
		capp = create_app(os.getenv('AC_CONFIG', 'beta'))
		db = SQLAlchemy(capp)
		session = db.session
	except:
		from prime import db
		session = db.session	
    
	for item in items:
		process_company(item, session)