from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask import Flask
from prime.utils import r
from difflib import SequenceMatcher
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

def has_common_institutions(p1,p2, intersect_threshold=5):
	from prime.prospects.models import LinkedinSchool, LinkedinCompany, LinkedinCompanyUrl
	common_schools = common_school_ids(p1,p2)
	if len(common_schools)>0: return "Attended " + session.query(LinkedinSchool).get(common_schools.pop()).name
	common_companies = common_company_ids(p1,p2)
	if len(common_companies)>0: return "Worked at " + session.query(LinkedinCompany).get(common_companies.pop()).name
	common_school = has_common_school_names(p1,p2, intersect_threshold=intersect_threshold)
	if common_school: return "Attended " + common_school
	common_company = has_common_company_names(p1,p2, intersect_threshold=intersect_threshold)
	if common_company: return "Worked at " + common_company
	return False

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

def name_match(name1, name2, intersect_threshold=2):
	name1 = re.sub('[^0-9a-z\s]','',name1.lower())
	name2 = re.sub('[^0-9a-z\s]','',name2.lower())
	name1_words = set(name1.split(" "))
	name2_words = set(name2.split(" "))
	stop_words = ["the", "of","and","a","the","at","for","in","on"]
	for stop_word in stop_words:
		if stop_word in name1_words: name1_words.remove(stop_word)
		if stop_word in name2_words: name2_words.remove(stop_word)	
	intersect = name1_words & name2_words
	intersect_threshold = min(intersect_threshold, len(name2_words))
	intersect_threshold = min(intersect_threshold, len(name2_words))
	if len(intersect)>=intersect_threshold: return True
	ratio = SequenceMatcher(None, name1, name2)
	if ratio>=0.8: return True
	return False	

def has_common_school_names(p1, p2, intersect_threshold=3):
	for school1 in p1.schools:
		if not school1.name: continue
		for school2 in p2.schools:
			if not school2.name: continue
			if name_match(school1.name, school2.name, intersect_threshold=intersect_threshold): 
				print school1.name + "-->" + school2.name
				if len(school2.name) < len(school1.name): return school2.name
				return school1.name
	return None

def has_common_company_names(p1, p2, intersect_threshold=3):
	for job1 in p1.jobs:
		if not job1.company or not job1.company.name: continue
		for job2 in p2.jobs:
			if not job2.company or not job2.company.name: continue
			if name_match(job2.company.name, job1.company.name, intersect_threshold=intersect_threshold): 
				print job2.company.name + "-->" + job1.company.name
				if len(job2.company.name) < len(job1.company.name): return job2.company.name
				return job1.company.name
	return None

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

def company_from_url(url, session=session):
	from prime.prospects.models import LinkedinCompany, LinkedinCompanyUrl
	companyUrl = session.query(LinkedinCompanyUrl).get(url)
	if companyUrl: 
		company = session.query(LinkedinCompany).get(companyUrl.company_id)
		if company: return company 
	return None

def from_url(url, session=session):
	from prime.prospects.models import Prospect, ProspectUrl
	prospectUrl = session.query(ProspectUrl).get(url)
	if prospectUrl: 
		prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(linkedin_id=prospectUrl.linkedin_id).first()
		if prospect: return prospect 
	if url.find("https:") > -1: url_new = url.replace("https:","http:")
	elif url.find("http:") > -1: url_new = url.replace("http:","https:")
	prospectUrl = session.query(ProspectUrl).get(url_new)
	if prospectUrl: 
		prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(linkedin_id=prospectUrl.linkedin_id).first()
		if prospect:
			session.add(ProspectUrl(url=url, linkedin_id=prospect.linkedin_id))
			session.commit()
			return prospect
	prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(s3_key=url.replace("/", "")).first()
	if prospect: 
		session.add(ProspectUrl(url=url, linkedin_id=prospect.linkedin_id))
		session.commit()
		return prospect
	prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(s3_key=url_new.replace("/", "")).first()
	if prospect: 
		session.add(ProspectUrl(url=url, linkedin_id=prospect.linkedin_id))
		session.commit()	
	else: r.sadd("urls",url)
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