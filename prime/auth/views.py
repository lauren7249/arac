import logging

from flask import redirect, request, url_for, flash, render_template, session \
as flask_session
from flask.ext.login import login_user, logout_user, current_user, fresh_login_required

from . import auth
from prime import db, csrf
from prime.customers.models import Customer
from .forms import SignUpForm, LoginForm
from prime.users.models import User


logger = logging.getLogger(__name__)

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
            return redirect("/")
    return render_template('auth/signup.html', signup_form=form)


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

