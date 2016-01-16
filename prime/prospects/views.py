import logging
from flask import Flask
from collections import Counter

from rq import Queue
from redis import Redis
import re
import random
import requests
import datetime
import json
from urllib import unquote_plus
from flask import render_template, request, redirect, url_for, flash, \
session as flask_session, jsonify
from flask.ext.login import current_user

from . import prospects
from prime.prospects.models import Prospect, Job, Education, get_or_create
from prime.users.models import ClientProspect
from prime import db, csrf
from prime.processing_service.constants import REDIS_URL
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast, extract, or_, func
from sqlalchemy.orm import joinedload, subqueryload, outerjoin
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

def get_q():
    conn = Redis(REDIS_URL, 6379)
    q = Queue('high',connection=conn)
    return q

def queue_processing_service(client_data, contacts_array):
    from prime.processing_service.processing_service import ProcessingService
    service = ProcessingService(client_data, contacts_array)
    service.process()
    return True

def after_contacts_uploaded(current_user, unique_emails, contacts_array):
    manager = current_user.manager
    to_email = manager.user.email
    client_data = {"first_name":current_user.first_name,"last_name":current_user.last_name,\
            "email":current_user.email,"location":current_user.linkedin_location,"url":current_user.linkedin_url,\
            "to_email":to_email}
    user_request = UserRequest(user_email)
    user_request._make_request(contacts_array)  
    current_user.unique_contacts_uploaded = unique_emails
    session.add(current_user)
    session.commit()
    env = Environment()
    env.loader = FileSystemLoader("prime/templates")                
    tmpl = env.get_template('emails/contacts_uploaded.html')
    body = tmpl.render(first_name=user.first_name, last_name=user.last_name, email=current_user.email)
    sendgrid_email(to_email, "{} {} imported contacts into AdvisorConnect".format(current_user.first_name, current_user.last_name), body)      
    service = ProcessingService(client_data, contacts_array)
    service.process()

################
##    VIEWS   ##
################

@prospects.route("/", methods=['GET', 'POST'])
def start():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    #User already has prospects, lets send them to the dashboard
    if current_user.unique_contacts_uploaded>0:
        return redirect(url_for('prospects.pending'))
    if current_user.has_prospects:
        return redirect(url_for('prospects.dashboard'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    return render_template('start.html')

@prospects.route("/pending", methods=['GET'])
def pending():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
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
        user_email = indata.get("user_email","")
        client_first_name = indata.get("firstName","")
        # f = open('data/{}.json'.format(user_email),'w')
        # f.write(json.dumps(indata)) 
        contacts_array = indata.get("contacts_array")  
        by_email = set()         
        for record in contacts_array:
            if len(str(record)) > 10000: 
                print "CloudspongeRecord is too big"
                continue
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
        q = get_q()
        q.enqueue(after_contacts_uploaded, current_user, n_contacts, contacts_array, timeout=140400)    
    return jsonify({"contacts": n_contacts})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))    
    if current_user.p200_completed:
        agent = current_user
        return render_template("dashboard.html", agent=agent, active = "dashboard")
    #should we show a non-hired agent their network?
    # if current_user.hiring_screen_completed:
    #     return render_template("dashboard.html", agent=agent, active = "dashboard")
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
        return self.sql_query.join(ClientProspect.prospect).filter(Prospect.industry_category==unquote_plus(self.industry))

    def _search(self):
        return self.sql_query.join(ClientProspect.prospect).filter(Prospect.name.ilike("%{}%".format(self.query)))

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

@csrf.exempt
@prospects.route("/connections", methods=['GET', 'POST'])
def connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))       
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    page = int(request.args.get("p", 1))
    agent = current_user
    connections = ClientProspect.query\
            .options(joinedload('prospect'))\
            .options(joinedload('prospect').joinedload('jobs'))\
            .options(joinedload('prospect').joinedload('schools'))\
            .filter(ClientProspect.extended==False, \
            ClientProspect.processed==False,
            ClientProspect.user==agent,
            ClientProspect.good==False,
            ClientProspect.stars>0,
            ).order_by(ClientProspect.lead_score.desc())
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
@prospects.route("/extended/connections", methods=['GET', 'POST'])
def extended_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))       
    if not current_user.p200_completed:
        return redirect(url_for('prospects.pending'))
    page = int(request.args.get("p", 1))
    agent = current_user
    connections = ClientProspect.query\
            .options(joinedload('prospect'))\
            .options(joinedload('prospect').joinedload('jobs'))\
            .options(joinedload('prospect').joinedload('schools'))\
            .filter(ClientProspect.extended==True, \
            ClientProspect.processed==False,
            ClientProspect.good==False,
            ClientProspect.user==agent,
            ClientProspect.stars>0,
            ).order_by(ClientProspect.lead_score.desc())
    query, industry, stars = get_args(request)
    search = SearchResults(connections, query=query, industry=industry,
            stars=stars)
    connections = search.results().paginate(page, 25, False)
    return render_template("connections.html",
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active="extended")

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

