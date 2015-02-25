from flask import Flask
import datetime
import json
import urllib
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask.ext.login import current_user

from . import users
from prime.prospects.models import Prospect, Job, Education, Company, School, \
Industry
from prime.users.models import ClientList, User
from prime.prospects.prospect_list import ProspectList
from prime import db, csrf

from consume.consumer import generate_prospect_from_url
from consume.convert import clean_url as _clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

from prime.prospects.helper import LinkedinResults
from prime.prospects.arequest import aRequest
from prime.search.search import SearchRequest

session = db.session

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

