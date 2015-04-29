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

from . import auth
from prime import db, csrf
from prime.customers.models import Customer
from .forms import SignUpForm, LoginForm
from prime.users.models import User


logger = logging.getLogger(__name__)

def get_view_redis(redis_url):
    urlparse.uses_netloc.append('redis')
    redis_url_parsed = urlparse.urlparse(redis_url)
    redis = Redis(
        host=redis_url_parsed.hostname,
        port=redis_url_parsed.port,
        db=0,
        password=redis_url_parsed.password
    )

    return redis


def linkedin_friends(username, password, user_id):

    data = {"username": username,
            "password": password,
            "user_id": user_id}
    redis_url = 'redis://linkedin-assistant.btwauj.0001.use1.cache.amazonaws.com:6379'
    print redis_url, "redis url"
    instance_id = boto.utils.get_instance_metadata()['local-hostname']
    print instance_id, "instance id"
    q = RedisQueue('linkedin-assistant', instance_id, redis=get_view_redis(redis_url))
    q.push(json.dumps(data), filter_seen=False, filter_failed=False, filter_working=False)
    return True

@auth.route('/auth/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous():
        return redirect(url_for('prospects.search'))
    form = LoginForm()
    valid = True
    if form.is_submitted():
        if form.validate():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.check_password(form.password.data):
                login_user(user)
                return redirect(request.args.get('next') or
                        url_for('prospects.upload'))
        valid = False
        form.email.data = ''
        form.password.data = ''
    return render_template('auth/login.html', form=form, valid=valid)

@auth.route('/auth/signup/<customer_slug>', methods=['GET', 'POST'])
def signup(customer_slug):
    customer = Customer.query.filter_by(slug=customer_slug).first()
    if not customer:
        return redirect(url_for('main.index'))
    form = SignUpForm()
    if form.is_submitted():
        if form.validate():
            newuser = User(form.first_name.data, form.last_name.data, form.email.data, form.password.data)
            newuser.customer = customer
            newuser.plan_id = 1
            db.session.add(newuser)
            db.session.commit()
            login_user(newuser, True)
            flask_session['first_time'] = True
            return redirect("/auth/signup/{}/linkedin".format(customer.slug))
    return render_template('auth/signup.html', signup_form=form)

@csrf.exempt
@auth.route('/auth/signup/<customer_slug>/linkedin', methods=['GET', 'POST'])
def signup_linkedin(customer_slug):
    customer = Customer.query.filter_by(slug=customer_slug).first()
    if not customer:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user_id = current_user.user_id
        result = linkedin_friends(email, password, user_id)
        return redirect("/")
    return render_template('auth/linkedin.html')


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


