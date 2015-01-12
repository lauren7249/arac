from flask import Flask
import urllib
from flask import render_template, request

from . import prospects
from prime.prospects.models import Prospect, Job, Education, Company, School
from prime.prospects.prospect_list import ProspectList
from prime import db

try:
    from consume.consume import generate_prospect_from_url
    from consume.convert import clean_url
    from consume.convert import parse_html
except:
    pass

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

@prospects.route("/", methods=['POST'])
def select_client():
    if request.method == 'POST':
        url = request.form.get("url")
        raw_html = aRequest(url)
    return render_template('upload.html', results=results)

@prospects.route("/search")
def search():
    results = None
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        prospect = generate_prospect_from_url(url)
        prospect_list = ProspectList(prospect)
        results = prospect_list.get_results()
    return render_template('search.html', results=results)

@prospects.route("/company/<int:company_id>")
def company(company_id):
    company = session.query(Company).get(company_id)
    jobs = session.query(Job).filter_by(company_id=company.id).limit(100)
    return render_template('company.html', company=company, jobs=jobs)

@prospects.route("/company/<int:school_id>")
def school(school_id):
    school = session.query(School).get(school_id)
    prospects = session.query(Prospect).filter_by(school=school)
    return render_template('school.html', school=school, prospects=prospects)

@prospects.route("/prospect/<int:prospect_id>")
def prospect(prospect_id):
    prospect = session.query(Prospect).get(prospect_id)
    jobs = prospect.jobs
    schools = prospect.schools
    return render_template('prospect.html', prospect=prospect, jobs=jobs,
            schools=schools)

print "made it"
