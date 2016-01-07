import logging
from flask import Flask
from collections import Counter

from rq import Queue
from redis import Redis
from rq import Queue
import re
import random
import requests
import datetime
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, \
session as flask_session, jsonify
from flask.ext.login import current_user

from . import prospects
from prime.prospects.models import Prospect, Job, Education, get_or_create
from prime.users.models import User, ClientProspect
from prime.managers.models import ManagerProfile
from prime import db, csrf

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast, extract
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import aliased

from flask.ext.rq import job

################
##  HELPERS   ##
################

session = db.session
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_url(s):
    pr = urlparse.urlparse(s)

    return urlparse.urlunparse((
        pr.scheme,
        pr.netloc,
        pr.path,
        '',
        '',
        ''
    ))

def uu(str):
    if str:
        try:
            return str.decode("ascii", "ignore").encode("utf-8")
        except:
            return str.encode('UTF-8')
    return None

################
##   TASKS    ##
################

def get_conn():
    return Redis()

def queue_processing_service(client_data, contacts_array):
    from prime.processing_service.processing_service import ProcessingService
    service = ProcessingService(client_data, contacts_array)
    service.process()
    return True

################
##    VIEWS   ##
################

@prospects.route("/", methods=['GET', 'POST'])
def start():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    #User already has prospects, lets send them to the dashboard
    if current_user.has_prospects:
        return redirect(url_for('prospects.dashboard'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    return render_template('start.html')

@prospects.route("/pending", methods=['GET'])
def pending():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    contact_count = request.args.get("contacts")
    return render_template('pending.html', contact_count=contact_count)

@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route("/upload_cloudsponge", methods=['GET', 'POST'])
def upload():
    unique_emails = set()
    if request.method == 'POST':
        first_name = request.json.get("firstName",)
        last_name = request.json.get("lastName")
        email = request.json.get("user_email","").lower()
        location = request.json.get("geolocation")
        url = request.json.get("public_url","").lower()
        image_url = request.json.get("image_url")
        manager = ManagerProfile.query.filter(\
                ManagerProfile.users.contains(current_user)).first()
        to_email = manager.user.email
        client_data = {"first_name":first_name,"last_name":last_name,\
                "email":current_user.email,"location":location,"url":url,\
                "to_email":to_email}
        contacts_array = request.json.get("contacts_array",[])
        for record in contacts_array:
            contact_email = record.get('contact').get("email", [{}])[0].get('address')
            unique_emails.add(contact_email)

        from prime.processing_service.saved_request import UserRequest
        user_request = UserRequest(current_user.email)
        user_request._make_request(contacts_array)
        conn = get_conn()
        current_user.image_url = image_url
        current_user.linkedin_url = url
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.linkedin_email = email
        current_user.linkedin_location = location
        session.add(current_user)
        session.commit()
        q = Queue(connection=conn)
        random.shuffle(contacts_array)
        f = open('data/bigtext.json','w')
        f.write(json.dumps(contacts_array))
        f.close()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=14400)
    return jsonify({"contacts": len(list(unique_emails))})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    agent = current_user
    return render_template("dashboard.html", agent=agent, active = "dashboard")


class SearchResults(object):

    def __init__(self, sql_query, query=None, rating=None, filter=None, *args, **kwargs):
        self.sql_query = sql_query
        self.query = query
        self.rating = rating
        self.filter = filter

    def _rating(self):
        return self.sql_query.filter(ClientProspect.stars == self.stars)

    def _filter(self):
        return self.sql_query.filter(Prospect.industry == self.filter)

    def _search(self):
        return self.sql_query.filter(
                Prospect.linkedin_name.like("%{}%".format(query)),
                Job.name.like("%{}%".format(query)),
                Education.name.like("%{}%".format(query))
                    )

    def results(self):
        if self.query:
            self.sql_query = self._search()
        if self.rating:
            self.sql_query = self._rating()
        if self.filter:
            self.sql_query = self._filter()
        return self.sql_query

@prospects.route("/connections", methods=['GET', 'POST'])
def connections():
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    agent = current_user
    connections = agent.prospects.filter(ClientProspect.extended==False).order_by(ClientProspect.lead_score.desc())
    return render_template("connections.html",
            agent=agent,
            connections=connections,
            active="connections")

@prospects.route("/extended/connections", methods=['GET', 'POST'])
def extended_connections():
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    agent = current_user
    connections = agent.prospects.filter(ClientProspect.extended==True).order_by(ClientProspect.lead_score.desc())
    return render_template("connections.html",
            agent=agent,
            connections=connections,
            active="extended")

