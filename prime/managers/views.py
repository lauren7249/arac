from flask import Flask
import hashlib
import random
import datetime
import requests
import json
import re
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
    if current_user.email == 'jimmy@advisorconnect.co':
        return redirect(url_for('managers.godview'))
    reinvited = request.args.get("reinvited",None)
    manager = current_user.manager_profile[0]
    agents = manager.users.filter(User.email.contains("@")).order_by(User.first_name, User.last_name, User.email)
    hired_agents = agents.filter(User.hired == True).all()
    candidates = agents.filter(User.hired == False, User.not_hired ==\
            False).all()
    not_hired = agents.filter(User.not_hired == True).all()
    return render_template('manager/dashboard.html',
            hired_agents=hired_agents,
            candidates=candidates,
            not_hired=not_hired,
            manager=manager,
            reinvited=reinvited,
            active="selected")

@manager.route('/godview', methods=['GET'])
def godview():
    if current_user.email != 'jimmy@advisorconnect.co':
        return redirect(url_for('auth.login'))
    reinvited = request.args.get("reinvited",None)
    manager = current_user.manager_profile[0]
    agents = User.query.filter(User.email.contains("@"), User.manager_id != 2,\
            User.manager_id != 8, User.manager_id != 10\
            ).order_by(User.first_name, User.last_name, User.email)
    hired_agents = agents.filter(User.hired == True).all()
    candidates = agents.filter(User.hired == False, User.not_hired ==\
            False).all()
    not_hired = agents.filter(User.not_hired == True).all()
    return render_template('manager/godview.html',
            hired_agents=hired_agents,
            candidates=candidates,
            not_hired=not_hired,
            manager=manager,
            reinvited=reinvited,
            active="selected")


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
        if not re.search(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", to_email):
            error_message = "{} is not a valid email address.".format(to_email)
            return render_template('manager/invite.html', active="invite", error_message=error_message,
                                   success=False)
        agent = session.query(User).filter(User.email == to_email).first()
        if agent:
            if agent.is_manager:
                error_message = "This candidate exists in our system as a manager, therefore you cannot invite them as " \
                                "an agent."
                return render_template('manager/invite.html', active="invite", error_message=error_message,
                                       success=False)
            if not agent.not_hired:
                error_message = "This candidate is still being evaluated by another manager, therefore you cannot invite them. For more information, feel free to email jeff@advisorconnect.co."
                return render_template('manager/invite.html', active="invite", error_message=error_message,
                                       success=False)
            user = agent
            #remove the user from their previous manager's dashboard.
            if user.manager:
                old_manager = user.manager
                old_manager.users.remove(user)
                session.add(old_manager)
                session.commit()
        else:
            user = User(first_name, last_name, to_email, '')
        manager = current_user.manager_profile[0]
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
    if not current_user.is_manager:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        user_id = int(request.form.get('user_id'))
        user = User.query.filter(User.user_id == user_id).first()
        user.invite()
    return redirect('/managers/dashboard?reinvited={}#prospective-agents'.format(user.email))


@manager.route("/agent/<int:agent_id>", methods=['GET', 'POST'])
def agent(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return redirect(url_for('auth.login'))
    agent = User.query.get(agent_id)
    manager = agent.manager
    if current_user.user_id != manager.user_id and current_user.email != 'jimmy@advisorconnect.co':
        return "You are not authorized to view this content."
    p200 = request.args.get("p200","False")
    if p200=="False":
        active = "dashboard"
    else:
        active = "p200_summary"
    return render_template("dashboard.html", agent=agent, active=active)


@csrf.exempt
@manager.route("/p200/<int:agent_id>", methods=['GET', 'POST'])
def agent_p200(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return redirect(url_for('auth.login'))
    page = int(request.args.get("p", 1))
    agent = User.query.get(agent_id)
    manager = agent.manager
    if current_user.user_id != manager.user_id:
        return "You are not authorized to view this content."
    if not agent.p200_submitted_to_manager:
        return "This agent has not yet submitted a p200 for you to view."
    connections = ClientProspect.query.filter(
        ClientProspect.good == True,
        ClientProspect.user == agent,
    ).join(Prospect).order_by(Prospect.name)
    connections = connections.paginate(page, 25, False)
    return render_template("p200.html",
                           agent=agent,
                           page=page,
                           connections=connections.items,
                           pagination=connections,
                           active="p200")


@csrf.exempt
@manager.route("/dashboard_pdf/<int:agent_id>", methods=['GET', 'POST'])
def dashboard_pdf(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return redirect(url_for('auth.login'))
    agent = User.query.get(agent_id)
    manager = agent.manager
    if current_user.user_id != manager.user_id:
        return "You are not authorized to view this content."
    p200 = request.args.get("p200","False")
    if p200=="False":
        active = "dashboard"
    else:
        active = "p200_summary"
    return render_template("print-network-summary.html", agent=agent, active=active)

@csrf.exempt
@manager.route("/pdf/<int:agent_id>", methods=['GET', 'POST'])
def pdf(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        logout_user()
        return redirect(url_for('auth.login'))
    page = int(request.args.get("p", 1))
    agent = User.query.get(agent_id)
    if not agent:
        return "Invalid link"
    manager = agent.manager
    if current_user.user_id != manager.user_id:
        return "You are not authorized to view this content."
    connections = ClientProspect.query.filter(
        ClientProspect.good == True,
        ClientProspect.user == agent,
    ).join(Prospect).order_by(Prospect.name)
    connections = connections.paginate(page, 200000, False)
    return render_template("pdf.html",
                           agent=agent,
                           page=page,
                           connections=connections.items,
                           pagination=connections,
                           active="pdf")


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
            client_data = {"first_name": user.first_name, "last_name": user.last_name, \
                           "email"     : user.email, "location": user.location, "url": user.linkedin_url, \
                           "to_email"  : to_email, "hired": True}
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
            return jsonify({"name": "{} {}".format(user.first_name, user.last_name)})
        except Exception, e:
            print str(e)


@manager.route("/approve/<int:agent_id>", methods=['GET', 'POST'])
def approve_p200(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return "You are not authorized to view this content."
    agent = User.query.get(agent_id)
    if agent.manager_id != current_user.manager_profile[0].manager_id:
        return "You are not authorized to view this content."
    agent.p200_manager_approved()
    agent.p200_approved = True
    session.add(agent)
    session.commit()
    return redirect(url_for('.agent_p200', agent_id=agent_id))

@manager.route("/make_agent/<int:agent_id>", methods=['GET', 'POST'])
def make_agent(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return "You are not authorized to view this content."
    agent = User.query.get(agent_id)
    if agent.manager_id != current_user.manager_profile[0].manager_id:
        return jsonify({"sucess": False})
    agent.hired = True
    session.add(agent)
    session.commit()
    return jsonify({"sucess": True})

@manager.route("/skip_agent/<int:agent_id>", methods=['GET', 'POST'])
def skip_agent(agent_id):
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.is_manager:
        return "You are not authorized to view this content."
    agent = User.query.get(agent_id)
    if agent.manager_id != current_user.manager_profile[0].manager_id:
        return jsonify({"sucess": False})
    reason = request.args.get("reason")
    agent.not_hired = True
    agent.not_hired_reason = reason
    session.add(agent)
    session.commit()
    return jsonify({"sucess": True})

