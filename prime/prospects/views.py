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
import io
import csv
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
from prime.users.models import User
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
from prime.utils.helpers import STATES

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
    if current_user.p200_approved:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_submitted_to_manager:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_completed:
        return redirect(url_for('prospects.connections'))
    if current_user.hiring_screen_completed:
        return redirect(url_for('prospects.dashboard'))
    #User already has prospects, lets send them to the dashboard
    if current_user.unique_contacts_uploaded>0:
        return redirect(url_for('prospects.pending'))
    return render_template('start.html', agent=current_user, newWindow='false')

@prospects.route("/pending", methods=['GET'])
def pending():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if current_user.p200_approved:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_submitted_to_manager:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_completed:
        return redirect(url_for('prospects.connections'))
    if current_user.hiring_screen_completed:
        return redirect(url_for('prospects.dashboard'))
    #User already has prospects, lets send them to the dashboard
    # if current_user.unique_contacts_uploaded>0:
    #     return render_template('pending.html', contact_count=current_user.unique_contacts_uploaded)
    return render_template('start.html', agent=current_user, newWindow='false')

@prospects.route("/faq")
def faq():
    return render_template('faq.html')

@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route("/save_linkedin_data", methods=['GET', 'POST'])
def save_linkedin_data():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
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
@prospects.route("/upload_csv", methods=['POST'])
def upload_csv():
    import pandas
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    f = request.files['file']
    if not f:
        return "No file"
    s = pandas.read_csv(f.stream)
    s.fillna("", inplace=True)
    data = []
    for index, row in s.iterrows():
        contact = {}
        contact["first_name"] = row["First Name"].decode('latin-1')
        contact["last_name"] = row["Last Name"].decode('latin-1')
        contact["companies"] = [row["Company"].decode('latin-1')]
        contact["email"] = [{"address": row["E-mail Address"].decode('latin-1')}]
        contact["job_title"] = row["Job Title"].decode('latin-1')
        data.append(contact)
    return jsonify({"count":len(s),"contacts":data, "contacts_owner":None})


@csrf.exempt
@prospects.route("/upload_cloudsponge", methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method == 'POST':
        indata = request.json
        contacts_array = indata.get("contacts_array")
        contacts_array, user = current_user.refresh_contacts(new_contacts=contacts_array)
        print len(contacts_array)
        manager = current_user.manager
        if not manager:
            print "Error: no manager for current_user {}".format(current_user.user_id)
            to_email = "missing_manager@advisorconnect.co"
        else:
            to_email = manager.user.email
        client_data = {"first_name":current_user.first_name,"last_name":current_user.last_name,\
                "email":current_user.email,"location":current_user.location,"url":current_user.linkedin_url,\
                "to_email":to_email}
        env = Environment()
        env.loader = FileSystemLoader("prime/templates")
        tmpl = env.get_template('emails/contacts_uploaded.html')
        body = tmpl.render(first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email)
        sendgrid_email(to_email, "{} {} has imported a total of {} contacts into AdvisorConnect".format(current_user.first_name, current_user.last_name, "{:,d}".format(user.unique_contacts_uploaded)), body)
        q = get_q()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=140400)
    return jsonify({"contacts": user.unique_contacts_uploaded})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.hiring_screen_completed:
        agent = current_user
        return render_template("dashboard.html", agent=agent, active = "dashboard")
    if current_user.unique_contacts_uploaded > 0:
        return redirect(url_for('prospects.pending'))
    return redirect(url_for('prospects.start'))

class SearchResults(object):

    def __init__(self, sql_query, query=None, stars=None, industry=None, state=None, *args, **kwargs):
        self.sql_query = sql_query
        self.query = query
        self.stars = stars
        self.industry = industry
        self.state = state

    def _stars(self):
        return self.sql_query.filter(ClientProspect.stars ==
                int(self.stars))

    def _industry(self):
        return self.sql_query.filter(Prospect.industry_category==unquote_plus(self.industry))

    def _state(self):
        return self.sql_query.filter(Prospect.us_state==unquote_plus(self.state))

    def _search(self):
        return self.sql_query.filter(Prospect.name.ilike("%{}%".format(self.query)))

    def results(self):
        if self.query:
           self.sql_query = self._search()
        if self.stars:
           self.sql_query = self._stars()
        if self.industry:
            self.sql_query = self._industry()
        if self.state:
            self.sql_query = self._state()
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
    state = get_or_none(request.args.get("state"))
    return query, industry, state, stars

FILTER_DICT = {
        'a-z': func.lower(Prospect.name),
        'z-a': func.lower(Prospect.name).desc()
        }

@csrf.exempt
@prospects.route("/connections", methods=['GET', 'POST'])
def connections():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if current_user.p200_approved:
        return redirect(url_for('prospects.p200'))
    if not current_user.p200_completed:
        if current_user.hiring_screen_completed:
            return redirect(url_for('prospects.dashboard'))
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
    query, industry, state, stars = get_args(request)
    search = SearchResults(connections, query=query, industry=industry, state=state, stars=stars)
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
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if not current_user.p200_completed:
        if current_user.hiring_screen_completed:
            return redirect(url_for('prospects.dashboard'))
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
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method != 'POST':
        return redirect(url_for('prospects.dashboard'))
    user = current_user
    p200_count = user.p200_count
    if request.form.get("multi"):
        ids = request.form.get("id").split(",")
        connection_ids = []
        for id in ids:
            if id.isdigit() and id != '':
                connection_ids.append(int(id))
        cp = ClientProspect.query.filter(ClientProspect.user==user,
                ClientProspect.prospect_id.in_(connection_ids))
        for c in cp:
            c.good = True
            session.add(c)
            session.commit()
            p200_count-=1
            if p200_count <= 0:
                return redirect(url_for("prospects.p200"))
    else:
        connection_id = request.form.get("id")
        prospect = Prospect.query.get(int(connection_id))
        cp = ClientProspect.query.filter(ClientProspect.user==user,\
                ClientProspect.prospect==prospect).first()
        cp.good = True
        session.add(cp)
        session.commit()
        p200_count-=1
        if p200_count <= 0:
            return redirect(url_for("prospects.p200"))
    return jsonify({"success":True})

@csrf.exempt
@prospects.route("/skip-connections", methods=['GET', 'POST'])
def skip_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method != 'POST':
        return redirect(url_for('prospects.dashboard'))
    user = current_user
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


@csrf.exempt
@prospects.route("/submit_p200_to_manager", methods=['GET', 'POST'])
def submit_p200_to_manager():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    #TODO disabling 50 connection rule.
    #if connections.count() < 50:
    #    return jsonify({"error": "You must have at least 50 connections"})
    agent.submit_to_manager()
    agent.p200_submitted_to_manager = True
    session.add(agent)
    session.commit()
    return jsonify({"success": True})




@prospects.route("/export", methods=['GET'])
def export():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)

    string_io = StringIO.StringIO()
    writer = csv.writer(string_io)
    headers = ["Prefix", "First Name", "Salutation (Preferred name, nickname)",
            "Last Name", "Suffix", "Email Address", "Address 1", "Address 2",
            "City", "State", "Zip Code", "Home Phone", "Other/Cell Phone",
            "Name of Business", "Fax Number"]
    writer.writerow(headers)
    for connection in connections:
        email1, email2, email3 = get_emails_from_connection(connection.prospect.email_addresses)
        name = connection.prospect.name
        try:
            state = STATES[connection.prospect.us_state]
        except:
            state = connection.prospect.us_state
        try:
            first_name, last_name = name.split(" ")
        except:
            try:
                first_name = name.split(" ")[0]
                last_name = " ".join(name.split(" ")[1:])
            except:
                first_name = name
                last_name = None
        row = ["", first_name, "", last_name, "", email1,
            "", "", connection.prospect.linkedin_location_raw,
            state, "", "", "",
            connection.prospect.company, ""]
        writer.writerow(row)
    output = make_response(string_io.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@csrf.exempt
@prospects.route("/pdf", methods=['GET', 'POST'])
def pdf():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    page = int(request.args.get("p", 1))
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    connections = connections.paginate(page, 20000, False)
    return render_template("pdf.html",
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active="pdf")

@csrf.exempt
@prospects.route("/intro_seen", methods=['GET', 'POST'])
def intro_seen():
    current_user.intro_js_seen = True
    session.add(current_user)
    session.commit()
    return jsonify({"success": True})

