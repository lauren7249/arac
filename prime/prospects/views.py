import logging
from flask import Flask
from collections import Counter

from rq import Queue
from redis import Redis
from rq import Queue

import random
import requests
import datetime
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, \
session as flask_session, jsonify
from flask.ext.login import current_user

from . import prospects
from prime.prospects.models import Prospect, Job, Education, Company, School, \
Industry, ProspectLocation, Location, ProspectGender, ProspectWealthscore
from prime.users.models import ClientList, User
from prime import db, csrf

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast, extract
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import aliased

from prime.prospects.helper import LinkedinResults
from prime.prospects.arequest import aRequest
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
        return str.decode("ascii", "ignore").encode("utf-8")
    return None

################
##   TASKS    ##
################

@job
def queue_processing_service(delay, user_email, public_url, data):
    from prime.processing_service.processing_service import ProcessingService
    service = ProcessingService(
            user_email=user_email,
            user_linkedin_url=public_url,
            csv_data=data)
    service.process()
    return True

################
##    VIEWS   ##
################

@prospects.route("/", methods=['GET', 'POST'])
def home():
    return render_template('start.html')

@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route("/upload_cloudsponge", methods=['GET', 'POST'])
def upload():
    unique_emails = set()
    if request.method == 'POST':
        results = []
        client_first_name = request.json.get("firstName")
        user_email = request.json.get("user_email")
        geolocation = request.json.get("geolocation")
        public_url = request.json.get("public_url")
        contacts_array = request.json.get("contacts_array")
        for c in contacts_array:
            if len(c.get("emails", [])) > 0:
                email = c.get("emails")[0].get("address", "").lower()
                unique_emails.add(email)

        queue_processing_service.delay(3, user_email,
                public_url, contacts_array)
    return jsonify({"unique_contacts": len(list(unique_emails))})
