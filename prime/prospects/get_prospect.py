from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask import Flask
import re, os, sys
try:
	from prime.prospects.prospect_list import *
	from consume.consumer import *
except:
	pass

from prime import create_app, db

def get_session():
	app = Flask(__name__)
	app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
	db = SQLAlchemy(app)
	session = db.session
	return session

session = get_session()

def has_common_institutions(p1,p2):
	return len(common_school_ids(p1,p2))>0 or len(common_company_ids(p1,p2))>0

def average_wealth_score(prospects):
	perc = [prospect.wealth_percentile() for prospect in prospects]
	tot = 0
	count = 0
	for p in perc:
		if p is None or p==0: continue
		tot += p
		count += 1
	average = tot/count
	return average

def common_school_ids(p1, p2):
	p1_school_ids = set()
	for school in p1.schools:
		if school.school_linkedin_id: p1_school_ids.add(school.school_linkedin_id)
	p2_school_ids = set()
	for school in p2.schools:
		if school.school_linkedin_id: p2_school_ids.add(school.school_linkedin_id)
	return p2_school_ids & p1_school_ids

def common_company_ids(p1, p2):
	p1_company_ids = set()
	for job in p1.jobs:
		if job.company_linkedin_id:  p1_company_ids.add(job.company_linkedin_id)
	p2_company_ids = set()
	for job in p2.jobs:
		if job.company_linkedin_id:   p2_company_ids.add(job.company_linkedin_id)
	return p2_company_ids & p1_company_ids

def from_linkedin_id(linkedin_id, session=session):
	from prime.prospects.models import Prospect, Job, Education
	prospect = session.query(Prospect).filter_by(linkedin_id=str(linkedin_id)).first()
	return prospect

def from_url(url, session=session):
	from prime.prospects.models import Prospect, ProspectUrl
	url = re.sub("https:","http:",url)
	prospectUrl = session.query(ProspectUrl).get(url)
	if prospectUrl:
		prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(linkedin_id=prospectUrl.linkedin_id).first()
	else:
		prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(s3_key=url.replace("/", "")).first()
	return prospect

def from_prospect_id(id, session=session):
	from prime.prospects.models import Prospect, Job, Education
	prospect = session.query(Prospect).get(id)
	return prospect


def update_network(url):
	prospect = update_prospect_from_url(url)
	p = ProspectList(prospect)
	plist = p.get_results()

	for d in plist:
		update_prospect_from_url(d.get("url"))

if __name__=="__main__":
	url = sys.argv[1]
	update_network(url)