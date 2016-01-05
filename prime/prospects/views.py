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
from prime.users.models import User
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
        client_data = {"first_name":first_name,"last_name":last_name, "email":email,"location":location,"url":url}      
        contacts_array = request.json.get("contacts_array",[])
        for record in contacts_array:
            contact_email = record.get("emails",[{}])[0].get("address", "").lower() 
            unique_emails.add(contact_email)       
        conn = get_conn()
        q = Queue(connection=conn)
        random.shuffle(contacts_array)
        f = open('data/bigtext.json','w')
        f.write(json.dumps(contacts_array))
        f.close()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=14400)
    return jsonify({"unique_contacts": len(list(unique_emails))})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    return render_template("dashboard.html")

