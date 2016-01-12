import logging
import hashlib
import boto
import json
import os
import urlparse
from redis import Redis

from flask import redirect, request, url_for, flash, render_template, session \
as flask_session
from flask.ext.login import login_user, logout_user, current_user, fresh_login_required

from . import auth
from prime import db, csrf
from prime.customers.models import Customer
from .forms import SignUpForm, LoginForm
from prime.users.models import User


logger = logging.getLogger(__name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous():
        return redirect(url_for('prospects.start'))
    form = LoginForm()
    valid = True
    if form.is_submitted():
        if form.validate():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user is not None and user.check_password(form.password.data):
                login_user(user)

                #If the user is a manager, lets take them to the manager
                #dashboard
                if user.is_manager:
                    return redirect(url_for('managers.manager_home'))
                return redirect(url_for('prospects.start'))

        valid = False
        form.email.data = ''
        form.password.data = ''
    return render_template('auth/login.html', form=form, valid=valid)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.is_submitted():
        if form.validate():
            code = form.code.data
            password = hashlib.md5(code).hexdigest()
            user = User.query.filter(User.onboarding_code == password).first()
            if user:
                user.onboarding_code = None
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                login_user(user, True)
                return redirect("/")
        print "ERROR:{}".format(form.errors)
        flash("The link you used has expired. Please request another \
                from your manager")
        return redirect(url_for('auth.login'))
    else:
        code = request.args.get("code")
        password = hashlib.md5(code).hexdigest()
        user = User.query.filter(User.onboarding_code == password).first()
        return render_template('auth/signup.html', signup_form=form, code=code)
    return redirect(url_for('auth.login'))


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


