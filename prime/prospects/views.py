from flask import Flask

from rq import Queue
from redis import Redis

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
Industry
from prime.users.models import ClientList, User
from prime.prospects.prospect_list import ProspectList
from prime import db, csrf

from consume.consumer import generate_prospect_from_url
from consume.convert import clean_url as _clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast
from sqlalchemy.orm import joinedload

from prime.prospects.helper import LinkedinResults
from prime.prospects.arequest import aRequest
from prime.search.search import SearchRequest
from services.exporter import Exporter

session = db.session
redis_conn = Redis()
q = Queue(connection=redis_conn)

################
###   TASKS   ##
################

def export_file(prospects, email):
    exporter = Exporter(prospects, email)
    exporter.export()
    return True


################
###   VIEWS   ##
################


@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route("/clients", methods=["GET", "POST"])
def clients():
    if request.method == 'POST':
        name = request.form.get("name")
        client_list = ClientList(user=current_user,
                name=name)
        session.add(client_list)
        session.commit()
        return redirect("/clients")
    client_lists = ClientList.query.filter_by(user=current_user).all()
    return render_template('clients.html', client_lists=client_lists)

@csrf.exempt
@prospects.route("/clients/<int:id>", methods=["GET", "POST"])
def clients_list(id):
    client_list = ClientList.query.get(id)
    prospects = client_list.prospects
    return render_template('clients/list.html', prospects=prospects,
            client_list=client_list)

@csrf.exempt
@prospects.route("/export", methods=["POST"])
def export():
    if request.method == 'POST':
        prospect_ids = request.form.get("ids").split(",")
        prospects = session.query(Prospect).filter(\
                Prospect.id.in_(prospect_ids))\
                .options(joinedload('jobs'), joinedload('jobs.company')).all()
        job = q.enqueue(export_file, prospects, current_user.email)
    return jsonify({"success": True})


@csrf.exempt
@prospects.route("/", methods=['GET', 'POST'])
def upload():
    if current_user.is_anonymous():
        return redirect(url_for('auth.login'))
    results = None
    if request.method == 'POST':
        query = request.form.get("query")
        results = LinkedinResults(query).process()
    else:
        if current_user.linkedin_url:
            return redirect("dashboard")
    return render_template('upload.html', results=results)

@csrf.exempt
@prospects.route("/select", methods=['POST'])
def select_profile():
    if request.method == 'POST':
        url = request.form.get("url")
        current_user.linkedin_url = url
        session.commit()
    return jsonify({"success": True})

@csrf.exempt
@prospects.route("/confirm", methods=['GET'])
def confirm_profile():
    if not current_user.linkedin_url:
        return redirect("select")
    prospect = Prospect.query.filter_by(url=current_user.linkedin_url).first()
    if request.method == 'POST':
        url = request.form.get("url")
        rq = aRequest(url)
        content = rq.get()
        url = content.get("prospect_url")
        if not current_user.linkedin_url:
            current_user.linkedin_url = url
            session.commit()
        return redirect("dashboard")
    return render_template('confirm.html', prospect=prospect)

@prospects.route("/dashboard")
def dashboard():
    first_time = False
    if 'first_time' in flask_session:
        first_time = True
        del flask_session['first_time']
    results = None
    linkedin_url = current_user.linkedin_url
    print current_user.linkedin_url
    raw_url = urllib.unquote(linkedin_url).decode('utf8')
    url = _clean_url(raw_url)
    prospect = session.query(Prospect).filter_by(s3_key=url.replace("/",
        "")).first()
    if not prospect:
        prospect = generate_prospect_from_url(url)
    prospect_list = ProspectList(prospect)
    results = prospect_list.get_results()
    if prospect.json:
        boosted_profiles = prospect.boosted_profiles
        if len(boosted_profiles) > 0:
            results = boosted_profiles + results
    school_count = prospect_list.prospect_school_count
    job_count = prospect_list.prospect_job_count
    return render_template('dashboard.html', results=results,
            prospect=prospect, school_count=school_count,
            job_count=job_count, json_results=json.dumps(results),
            first_time=first_time, prospect_count=len(results))

@prospects.route("/company/<int:company_id>")
def company(company_id):
    page = int(request.args.get("p", 1))
    company = session.query(Company).get(company_id)
    jobs = Job.query.filter_by(company_id=company_id).paginate(page, 50,
            False)
    return render_template('company.html', company=company, jobs=jobs)

@prospects.route("/school/<int:school_id>")
def school(school_id):
    page = int(request.args.get("p", 1))
    school = session.query(School).get(school_id)
    educations = Education.query.filter_by(school_id=school.id).paginate(page,
            50, False)
    return render_template('school.html', school=school, educations=educations)

@prospects.route("/prospect/<int:prospect_id>")
def prospect(prospect_id):
    prospect = session.query(Prospect).get(prospect_id)
    jobs = prospect.jobs
    schools = prospect.schools
    return render_template('prospect.html', prospect=prospect, jobs=jobs,
            schools=schools)

@prospects.route("/ajax/prospect/<int:prospect_id>")
def ajax_prospect(prospect_id):
    prospect = Prospect.query.get(prospect_id)
    client_lists = ClientList.query.filter_by(user=current_user)
    return jsonify({"prospect":prospect.to_json,
        "client_lists": [{"id": cl.id, "name": cl.name} for cl in client_lists]})

@prospects.route("/ajax/pipl/<int:prospect_id>")
def ajax_pipl(prospect_id):
    prospect = Prospect.query.get(prospect_id)
    return jsonify(prospect.pipl_info)

@csrf.exempt
@prospects.route("/educations/create", methods=['GET', 'POST'])
def educations_create():
    if request.method == 'POST':
        school_id = request.form.get("school_id")
        school = School.query.get(school_id)
        if not school:
            school = School.query.first()
        prospect = Prospect.query.filter_by(url=current_user.linkedin_url).first()
        start_date = request.form.get("start_date")
        end_date = request.form.get("start_date")
        degree = request.form.get("degree")
        new_education = Education(
                prospect = prospect,
                school = school,
                degree = degree,
                start_date = start_date,
                end_date = end_date
                )
        session.add(new_education)
        session.commit()
        return redirect("confirm")

@csrf.exempt
@prospects.route("/jobs/create", methods=['GET', 'POST'])
def jobs_create():
    if request.method == 'POST':
        company_id = request.form.get("company_id")
        company = Company.query.get(company_id)
        if not company:
            company = Company.query.first()
        prospect = Prospect.query.filter_by(url=current_user.linkedin_url).first()
        start_date = request.form.get("start_date")
        end_date = request.form.get("start_date")
        title = request.form.get("title")
        new_job = Job(
                prospect = prospect,
                company = company,
                title = title,
                start_date = start_date,
                end_date = end_date
                )
        session.add(new_job)
        session.commit()
        return redirect("confirm")


@prospects.route("/elastic_search")
def elastic_search():
    type = request.args.get("type", "school")
    term = request.args.get("term")
    search = SearchRequest(term, type=type)
    data = search.search()
    return render_template('ajax/search.html', results=data)

@csrf.exempt
@prospects.route("/investor_profile", methods=['GET', 'POST'])
def investor_profile():
    industries = Industry.query.all()
    if request.method == 'POST':
        locations = request.form.get("locations")
        industries = request.form.get("industries")
        gender = request.form.get("gender")
        return redirect("dashboard")
    return render_template('investor_profile.html', industries=industries)

@prospects.route("/search", methods=['GET'])
def search_view():
    page = int(request.args.get("p", 1))
    company_id = request.args.get("company_id", None)
    school_id = request.args.get("school_id", None)
    start_date = datetime.datetime.strptime(request.args.get("start_date", \
        "1900-01-01"), "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(request.args.get("end_date", \
            "2016-01-01"), "%Y-%m-%d").date()
    prospects = []
    prospect_results = []
    if company_id:
        prospects = session.query(Prospect, Job).distinct(Prospect.name)\
                .join(Job).filter_by(company_id=company_id)
        if start_date:
            prospects = prospects.join(Job).filter(Job.start_date>=start_date)
        if end_date:
            prospects = prospects.join(Job).filter(Job.end_date<=end_date)
    if school_id:
        prospects = session.query(Prospect, Education).distinct(Prospect.name).join(Education)\
                .filter_by(school_id=school_id)
        if start_date:
            prospects = prospects.join(Education).filter(Education.start_date>=start_date)
        if end_date:
            prospects = prospects.join(Education).filter(Education.end_date<=end_date)
    for prospect in prospects:
        setattr(prospect[0], "relevant_item", prospect[1])
        prospect_results.append(prospect[0])
    number = 50 * (page - 1)
    return render_template("search.html", \
            prospects=prospect_results[number:number+50])
