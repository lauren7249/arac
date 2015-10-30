import logging
import boto
import json
import os
import urlparse
from redis import Redis

from flask import redirect, request, url_for, flash, render_template, session \
as flask_session
from flask.ext.login import login_user, logout_user, current_user, fresh_login_required

from redis_queue import RedisQueue

from . import main


logger = logging.getLogger(__name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@main.route('/', methods=['GET', 'POST'])
def login():
    return render_template('index.html')

@main.route('/', methods=['GET', 'POST'])
def results():
    return render_template('index.html')

@main.route('/', methods=['GET', 'POST'])
def results():
    return render_template('index.html')
