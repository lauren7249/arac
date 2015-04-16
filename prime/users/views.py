from flask import Flask
import datetime
import requests
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask.ext.login import current_user

from . import users
from prime.prospects.models import Prospect, Job, Education, Company, School, \
Industry
from prime.users.models import ClientList, User, ClientProspect
from prime.prospects.prospect_list import ProspectList
from prime import db, csrf

try:
    from consume.consumer import generate_prospect_from_url
    from consume.convert import clean_url as _clean_url
except:
    pass

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

from prime.prospects.helper import LinkedinResults
from prime.prospects.arequest import aRequest
from prime.search.search import SearchRequest
from services.email_finder import EmailFinder

session = db.session

##############
##  TASKS   ##
#############

def get_email_and_vibe(prospect):
    data = prospect.json
    if not data:
        data = {}
    if 'pipl_and_vibe' in data: 
        return True
    data['pipl_and_vibe'] = True
    try:
        email_finder = EmailFinder(prospect.name, prospect.current_job.company.name, prospect.linkedin_id)
        email = email_finder.find_contact_information()
    except:
        email = None
    data['email'] = email
    if email:
        url = "https://vibeapp.co/api/v1/initial_data/?"
        key = "api_key=e0978324d7ac8b759084aeb96c5d7fde&"
        email="email={}&force=1".format(email)
        result = requests.get("".join([url, key, email]))
        vibe_json = json.loads(result.content)
        data['vibe'] = vibe_json
    session.query(Prospect).filter_by(id=prospect.id).update({"json":
        data})
    session.commit()
    return True

##############
##  VIEWS  ##
#############


@csrf.exempt
@users.route("/user/skills/add", methods=["GET", "POST"])
def user_skills_add():
    user = current_user
    if request.method == 'POST':
        skill = request.form.get('skill').lower()
        user_json = user.json
        if user.json:
            skills = user_json.get("skills", [])
            skills.append(skill)
            user_json['skills'] = skills
            user.json = user_json
            session.query(User).filter_by(user_id=user.user_id).update({"json":
                user_json})
            session.commit()
        else:
            user.json = {"skills": [skill]}
            session.commit()
        user = session.query(User).get(user.user_id)
        return jsonify({"skills": user.json.get("skills")})

@csrf.exempt
@users.route("/user/skills/delete", methods=["GET", "POST"])
def user_skills_delete():
    user = current_user
    if request.method == 'POST':
        skill = request.form.get('skill').lower()
        user_json = user.json
        if user.json:
            new_skills = []
            skills = user_json.get("skills", [])
            skills.remove(skill)
            user_json['skills'] = skills
            user.json = user_json
            session.query(User).filter_by(user_id=user.user_id).update({"json":
                user_json})
            session.commit()
        return jsonify({"skills": user.json.get("skills")})

@csrf.exempt
@users.route("/user/prospect/add/<int:prospect_id>", methods=["POST"])
def add_prospect_client_list(prospect_id):
    user = current_user
    if request.method == 'POST':
        name = datetime.date.today().strftime("%A, %b %d %Y")
        client_list = ClientList.query.filter_by(name=name,
                user=current_user).first()
        if not client_list:
            client_list = ClientList(name=name, user=current_user)
            session.add(client_list)
            session.commit()
        prospect = Prospect.query.get(prospect_id)
        result = get_email_and_vibe(prospect)
        today = datetime.date.today()
        client_prospect = ClientProspect(client_list=client_list,
                prospect=prospect, created=today)
        session.add(client_prospect)
        session.commit()
        user_json = user.json if user.json else {}
        good_profiles = user_json.get('good_profiles', [])
        good_profiles.append(prospect_id)
        user_json['good_profiles'] = good_profiles
        session.query(User).filter_by(user_id=user.user_id).update({"json":
            user_json})
        session.commit()
    return jsonify({"success": True})


@csrf.exempt
@users.route("/user/prospect/skip/<int:prospect_id>", methods=["POST"])
def skip_prospect(prospect_id):
    user = current_user
    if request.method == 'POST':
        user_json = user.json if user.json else {}
        skipped_profiles = user.json.get('skipped_profiles', [])
        skipped_profiles.append(prospect_id)
        user_json['skipped_profiles'] = skipped_profiles
        session.query(User).filter_by(user_id=user.user_id).update({"json":
            user_json})
        session.commit()
    return jsonify({"success": True})


@users.route("/api/clientlists")
def api_clientlists():
    page = 1
    user = current_user
    client_lists = ClientList.query.filter_by(user=current_user).all()
    results = []
    for list in client_lists:
        d={}
        d['name'] =list.name
        d['data'] = [p.to_json() for p in list.prospects]
        results.append(d)
    return jsonify({"success": results})

