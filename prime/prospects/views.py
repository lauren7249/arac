import logging
import StringIO
import csv
from flask import Flask
from collections import Counter
import socket
from rq import Queue
from redis import Redis
import re
import os
import random
import requests
import datetime
import json
from urllib import unquote_plus
from flask import render_template, request, redirect, url_for, flash, session as flask_session, jsonify, make_response
from flask.ext.login import current_user,  logout_user
from . import prospects
from prime.prospects.models import Prospect, Job, Education, get_or_create
from prime import db, csrf, whoisthis
from prime.processing_service.constants import REDIS_URL
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast, extract, or_, func
from sqlalchemy.orm import joinedload, subqueryload, outerjoin
from sqlalchemy.orm import aliased
from flask.ext.rq import job
from jinja2.environment import Environment
from jinja2 import FileSystemLoader
from prime.users.models import ClientProspect
from prime.utils.email import sendgrid_email

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

def get_q():
    if socket.gethostname() == 'docker':
        conn = Redis.from_url(url=REDIS_URL, db=0)
    else:
        conn = Redis.from_url(url='redis://localhost', db=0)
    q = Queue('high',connection=conn)
    return q

def queue_processing_service(client_data, contacts_array):
    from prime.processing_service.processing_service import ProcessingService
    service = ProcessingService(client_data, contacts_array)
    service.process()
    return True

################
##    VIEWS   ##
################

#@whoisthis
@prospects.route("/", methods=['GET', 'POST'])
def start():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if current_user.p200_completed or current_user.hiring_screen_completed:
        return redirect(url_for('prospects.dashboard'))
    #User already has prospects, lets send them to the dashboard
    if current_user.unique_contacts_uploaded>0:
        return redirect(url_for('prospects.pending'))
    return render_template('start.html')

@prospects.route("/pending", methods=['GET'])
def pending():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.hiring_screen_completed:
        return redirect(url_for("prospects.dashboard"))
    return render_template('pending.html', contact_count=current_user.unique_contacts_uploaded)

@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route("/save_linkedin_data", methods=['GET', 'POST'])
def save_linkedin_data():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        first_name = request.json.get("firstName",)
        last_name = request.json.get("lastName")
        email = request.json.get("emailAddress","").lower()
        location = request.json.get("location",{}).get("name")
        url = request.json.get('publicProfileUrl',"").lower()
        image_url = request.json.get("pictureUrl")
        industry = request.json.get("industry")
        current_user.image_url = image_url
        current_user.linkedin_url = url
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.linkedin_email = email
        current_user.linkedin_location = location
        current_user.linkedin_industry = industry
        session.add(current_user)
        session.commit()
    return jsonify(request.json)

@csrf.exempt
@prospects.route("/upload_cloudsponge", methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        indata = request.json
        contacts_array = indata.get("contacts_array")
        by_email = set()
        n_linkedin = 0
        n_gmail = 0
        n_yahoo = 0
        n_windowslive = 0
        account_sources = {}
        for record in contacts_array:
            if len(str(record)) > 10000:
                print "CloudspongeRecord is too big"
                continue
            owner = record.get("contacts_owner")
            if owner:
                account_email = owner.get("email",[{}])[0].get("address","").lower()
            else:
                account_email = "linkedin"
            service = record.get("service","").lower()
            account_sources[account_email] = service
            if service=='linkedin':
                n_linkedin+=1
            elif service=='gmail':
                n_gmail+=1
            elif service=='yahoo':
                n_yahoo+=1
            elif service=='windowslive':
                n_windowslive+=1
            contact = record.get("contact",{})
            emails = contact.get("email",[{}])
            try:
                email_address = emails[0].get("address",'').lower()
            except Exception, e:
                email_address = ''
                print str(e)
            if email_address:
                by_email.add(email_address)
        n_contacts = len(by_email)
        current_user.unique_contacts_uploaded = n_contacts
        current_user.contacts_from_linkedin = n_linkedin
        current_user.contacts_from_gmail = n_gmail
        current_user.contacts_from_yahoo = n_yahoo
        current_user.contacts_from_windowslive = n_windowslive
        current_user.account_sources = account_sources
        session.add(current_user)
        session.commit()
        manager = current_user.manager
        if not manager:
            print "Error: no manager for current_user {}".format(current_user.user_id)
            to_email = "missing_manager@advisorconnect.co"
        else:
            to_email = manager.user.email
        client_data = {"first_name":current_user.first_name,"last_name":current_user.last_name,\
                "email":current_user.email,"location":current_user.linkedin_location,"url":current_user.linkedin_url,\
                "to_email":to_email}
        from prime.processing_service.saved_request import UserRequest
        user_request = UserRequest(current_user.email)
        user_request._make_request(contacts_array)
        print user_request.boto_key.key
        print user_request.boto_key.exists()
        env = Environment()
        env.loader = FileSystemLoader("prime/templates")
        tmpl = env.get_template('emails/contacts_uploaded.html')
        body = tmpl.render(first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email)
        sendgrid_email(to_email, "{} {} imported {} contacts into AdvisorConnect".format(current_user.first_name, current_user.last_name, "{:,d}".format(n_contacts)), body)
        q = get_q()
        print q.connection
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=140400)
    return jsonify({"contacts": n_contacts})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.p200_completed or current_user.hiring_screen_completed:
        agent = current_user
        return render_template("dashboard.html", agent=agent, active = "dashboard")
    if current_user.unique_contacts_uploaded > 0:
        return redirect(url_for('prospects.pending'))
    return redirect(url_for('prospects.start'))

class SearchResults(object):

    def __init__(self, sql_query, query=None, stars=None, industry=None, *args, **kwargs):
        self.sql_query = sql_query
        self.query = query
        self.stars = stars
        self.industry = industry

    def _stars(self):
        return self.sql_query.filter(ClientProspect.stars ==
                int(self.stars))

    def _industry(self):
        return self.sql_query.filter(Prospect.industry_category==unquote_plus(self.industry))

    def _search(self):
        return self.sql_query.filter(Prospect.name.ilike("%{}%".format(self.query)))

    def results(self):
        if self.query:
           self.sql_query = self._search()
        if self.stars:
           self.sql_query = self._stars()
        if self.industry:
            self.sql_query = self._industry()
        return self.sql_query

def get_or_none(item):
    if not item:
        return None
    if item.strip() == "":
        return None
    return item

def get_args(request):
    query = get_or_none(request.args.get("query"))
    industry = get_or_none(request.args.get("industry"))
    stars = get_or_none(request.args.get("stars"))
    return query, industry, stars

FILTER_DICT = {
        'a-z': func.lower(Prospect.name),
        'z-a': func.lower(Prospect.name).desc()
        }

@csrf.exempt
@prospects.route("/connections", methods=['GET', 'POST'])
def connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login')) 
    if current_user.hiring_screen_completed:
        return redirect(url_for('prospects.dashboard'))              
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    page = int(request.args.get("p", 1))
    order = request.args.get("order", "a-z")
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.processed==False,
            ClientProspect.user==agent,
            ClientProspect.good==False,
            ClientProspect.stars>0,
            ).join(Prospect).order_by(FILTER_DICT[order])
    if connections.filter(ClientProspect.extended==False).count() > 1:
        connections = connections.filter(ClientProspect.extended == False)
    query, industry, stars = get_args(request)
    search = SearchResults(connections, query=query, industry=industry,
            stars=stars)
    connections = search.results().paginate(page, 25, False)
    return render_template("connections.html",
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active="connections")

@csrf.exempt
@prospects.route("/p200", methods=['GET', 'POST'])
def p200():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    page = int(request.args.get("p", 1))
    agent = current_user
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
@prospects.route("/add-connections", methods=['GET', 'POST'])
def add_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    user = current_user
    if request.method == 'POST':
        if request.form.get("multi"):
            connection_ids = [int(i) for i in request.form.get("id").split(",")]
            cp = ClientProspect.query.filter(ClientProspect.user==user,
                    ClientProspect.prospect_id.in_(connection_ids))
            for c in cp:
                c.good = True
                session.add(c)
            session.commit()
        else:
            connection_id = request.form.get("id")
            prospect = Prospect.query.get(int(connection_id))
            cp = ClientProspect.query.filter(ClientProspect.user==user,\
                    ClientProspect.prospect==prospect).first()
            cp.good = True
            session.add(cp)
            session.commit()
        return jsonify({"success":True})
    return jsonify({"success":False})

@csrf.exempt
@prospects.route("/skip-connections", methods=['GET', 'POST'])
def skip_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    user = current_user
    if request.method == 'POST':
        if request.form.get("multi"):
            connection_ids = [int(i) for i in request.form.get("id").split(",")]
            cp = ClientProspect.query.filter(ClientProspect.user==user,
                    ClientProspect.prospect_id.in_(connection_ids))
            for c in cp:
                c.processed = True
                session.add(c)
            session.commit()
        else:
            connection_id = request.form.get("id")
            prospect = Prospect.query.get(int(connection_id))
            cp = ClientProspect.query.filter(ClientProspect.user==user,\
                    ClientProspect.prospect==prospect).first()
            cp.processed = True
            session.add(cp)
            session.commit()
        return jsonify({"success":True})
    return jsonify({"success":False})

def get_emails_from_connection(emails):
    if not emails:
        return None, None, None
    if len(emails) == 0:
        return None, None, None
    if len(emails) == 1:
        return emails[0], None, None
    if len(emails) == 2:
        return emails[0], emails[1], None
    return emails[0], emails[1], emails[2]


@prospects.route("/submit_p200_to_manager", methods=['GET', 'POST'])
def submit_p200_to_manager():
    if not current_user.is_authenticated():
        return jsonify({"error": "You must be authenticated"})
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    if connections.count() < 50:
        return jsonify({"error": "You must have at least 50 connections"})
    agent.submit_to_manager()
    agent.p200_submitted_to_manager = True
    session.add(agent)
    session.commit()
    return jsonify({"success": True})




@prospects.route("/export", methods=['GET'])
def export():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)

    string_io = StringIO.StringIO()
    writer = csv.writer(string_io)
    headers = ["Name", "Occupation", "Email1", "Email2", "Email3", "Business Phone",
            "Location", "State", "Facebook", "Linkedin", "Gender",
            "Age","Colleges", "Industry", "Name Of Business"]
    writer.writerow(headers)
    for connection in connections:
        email1, email2, email3 = get_emails_from_connection(connection.prospect.email_addresses)
        row = [connection.prospect.name, connection.prospect.job,\
                email1, email2, email3, connection.prospect.phone,\
                connection.prospect.linkedin_location_raw,\
                connection.prospect.us_state, connection.prospect.facebook,\
                connection.prospect.linkedin_url,connection.prospect.gender,\
                connection.prospect.age, connection.prospect.school_names,\
                connection.prospect.linkedin_industry_raw,\
                connection.prospect.company]
        writer.writerow(row)
    output = make_response(string_io.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

