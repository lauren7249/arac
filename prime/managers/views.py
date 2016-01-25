from flask import Flask
import hashlib
import random
import datetime
import requests
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, session, \
jsonify, current_app
from flask.ext.login import current_user, login_required

from rq import Queue
from redis import Redis
from rq import Queue

from . import manager
from prime.prospects.models import Prospect, Job, Education
from prime.users.models import User, ClientProspect
from prime.utils import random_string
from prime import db, csrf, whoisthis

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
            agent_count=int(agent_count), active="selected")

@manager.route('/invite', methods=['GET', 'POST'])
def manager_invite_agent():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    error_message = None
    success = None
    if not current_user.is_manager:
        response = {"error": "Forbidden"}
        return jsonify(response)
    if request.method == 'POST':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        to_email = request.form.get("email").lower()
        agent = User.query.filter(User.email == to_email).first()
        if agent:
            error_message = "This agent already exists in our system. Please \
                    contact jeff@adivsorconnect.co if this seems incorrect to you"
        else:
            manager = current_user.manager_profile[0]
            user = User(first_name, last_name, to_email, '')
            user.manager_id = manager.manager_id
            session.add(user)
            session.commit()
            manager.users.append(user)
            session.add(manager)
            session.commit()
            user.invite()
            success = True
    return render_template('manager/invite.html', active="invite",
            error_message=error_message, success=success)

@csrf.exempt
@manager.route('/invite/again', methods=['GET', 'POST'])
def manager_reinvite_agent():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        user_id = int(request.form.get('user_id'))
        user = User.query.filter(User.user_id == user_id).first()
        user.invite()
    return jsonify({"sucess": True})

@manager.route("/agent/<int:agent_id>", methods=['GET', 'POST'])
def agent(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    agent = User.query.get(agent_id)
    manager = agent.manager
    if current_user.user_id != manager.user_id:
        return "You are not authorized to view this content."
    return render_template("dashboard.html", agent=agent, active = "agent_page")

@csrf.exempt
@manager.route("/p200/<int:agent_id>", methods=['GET', 'POST'])
def agent_p200(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    page = int(request.args.get("p", 1))
    agent = User.query.get(agent_id)
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    connections = connections.paginate(page, 25, False)
    return render_template("p200.html",
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active="p200")

@csrf.exempt
@manager.route("/request_p200", methods=['GET', 'POST'])
def request_p200():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        try:
            user_id = int(request.form.get('user_id'))
            user = User.query.get(user_id)
            manager = user.manager
            to_email = manager.user.email
            client_data = {"first_name":user.first_name,"last_name":user.last_name,\
                    "email":user.email,"location":user.linkedin_location,"url":user.linkedin_url,\
                    "to_email":to_email, "hired": True}
            from prime.processing_service.saved_request import UserRequest
            user_request = UserRequest(user.email)
            contacts_array = user_request.lookup_data()
            from prime.prospects.views import queue_processing_service, get_q
            user.p200_started = True
            session.add(user)
            session.commit()
            q = get_q()
            q.enqueue(queue_processing_service, client_data, contacts_array,
                        timeout=140400)
            return jsonify({"name": "{} {}".format(user.first_name, user.last_name) })
        except Exception, e:
            print str(e)

@manager.route("/approve/<int:agent_id>", methods=['GET', 'POST'])
def approve_p200(agent_id):
    if not current_user.is_authenticated():
        return jsonify({"error": "You must be authenticated"})
    agent = User.query.get(agent_id)
    agent.p200_manager_approved()
    agent.p200_approved = True
    session.add(agent)
    session.commit()
    return redirect(url_for('.agent_p200', agent_id=agent_id))

@manager.route("/test_email", methods=['GET'])
def test_email():
    return render_template("emails/invite.html", invited_by=current_user.name,
            )
