from flask import Flask
import urllib
from flask import render_template, request, redirect

from . import prospects
from prime.prospects.models import Prospect, Job, Education, Company, School
from prime.prospects.prospect_list import ProspectList
from prime import db

from consume.consumer import generate_prospect_from_url
from consume.convert import clean_url as _clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

from prime.prospects.helper import LinkedinResults
from prime.prospects.arequest import aRequest

session = db.session

@prospects.route("/clients")
def clients():
    pass

@prospects.route("/", methods=['GET', 'POST'])
def upload():
    results = None
    if request.method == 'POST':
        query = request.form.get("query")
        results = LinkedinResults(query).process()
    return render_template('upload.html', results=results)

@prospects.route("/select", methods=['POST'])
def select_client():
    if request.method == 'POST':
        url = request.form.get("url")
        rq = aRequest(url)
        url = rq.get().get("prospect_url")
        return redirect("/search?url=" + url)

@prospects.route("/search")
def search():
    results = None
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = _clean_url(raw_url)
        prospect = session.query(Prospect).filter_by(s3_key=url.replace("/",
            "")).first()
        if not prospect:
            prospect = generate_prospect_from_url(url)
        prospect_list = ProspectList(prospect)
        results = prospect_list.get_results()
        print prospect
    return render_template('search.html', results=results, prospect=prospect)

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

print "made it"
