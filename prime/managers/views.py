from flask import Flask
import hashlib
import random
import sendgrid
import datetime
import requests
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, session, \
jsonify, current_app
from flask.ext.login import current_user, login_required

from . import manager
from prime.prospects.models import Prospect, Job, Education, Company, School, \
Industry
from prime.users.models import User, ClientProspect
from prime.prospects.prospect_list import ProspectList
from prime.utils.email import sendgrid_email
from prime.utils import random_string
from prime import db, csrf

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast


session = db.session

##############
##  VIEWS  ##
#############

@manager.route('/dashboard', methods=['GET'])
def manager_home():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return redirect(url_for('prospects.dashboard'))
    manager = current_user.manager_profile[0]
    agents = manager.users.all()
    agent_count = manager.users.count()
    return render_template('manager/dashboard.html', agents=agents,
            agent_count=int(agent_count))

@manager.route('/invite', methods=['POST'])
def manager_invite_agent():
    if not current_user.is_manager:
        response = {"error": "Forbidden"}
        return jsonify(response)
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    to_email = request.form.get("email").lower()

    agent = User.query.filter(User.email == to_email).first()
    if agent:
        error_message = "This agent already exists in our system. Please \
                contact jeff@adivsorconnect if this seems incorrect to you"
        response = {"error": error_message}
        return jsonify(response)
    else:
        code = random_string(10).encode('utf-8')
        password = hashlib.md5(code).hexdigest()
        user = User(first_name, last_name, to_email, password)
        user.onboarding_code = password
        session.add(user)
        session.commit()
        manager = current_user.manager_profile[0]
        manager.users.append(user)
        session.add(manager)
        session.commit()
    body = render_template("emails/invite.html", invited_by=current_user.name,
            base_url=current_app.config.get("BASE_URL"), code=code)
    subject = "Your Advisorconnect Account is Ready!"
    sendgrid_email(to_email, subject, body)
    return jsonify({"success": True})

@manager.route("/test_email", methods=['GET'])
def test_email():
    return render_template("emails/invite.html", invited_by=current_user.name,
            )
