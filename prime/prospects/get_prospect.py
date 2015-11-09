from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask import Flask
from prime.utils import r
from difflib import SequenceMatcher
import pdb

import datetime
import re, os, sys
try:
	from prime.prospects.prospect_list import *
	from consume.consumer import *
except:
	pass

from prime import create_app, db

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

session = db.session

def connected(tup):
        session = get_session()
	p1 = tup[0]
	p2 = tup[1]
	if not p1 or not p2:
		return None
	# if not also_viewed(p1,p2):
	# 	print uu(p1.url + " not also viewed for " + p2.url)
	# 	return None
	return has_common_institutions(p1,p2)

def also_viewed(p1,p2):
	if not p1 or not p2:
		return False
	if p1.json and p1.json.get("people") and p2.url in p1.json.get("people"):
		return True
	if p2.json and p2.json.get("people") and p1.url in p2.json.get("people"):
		return True
	if p1.json and p1.json.get("people"):
		for url in p1.json.get("people"):
			p1_viewed = from_url(url)
			if not p1_viewed:
				continue
			if p1_viewed.id == p2.id:
				return True
	if p2.json and p2.json.get("people"):
		for url in p2.json.get("people"):
			p2_viewed = from_url(url)
			if not p2_viewed:
				continue
			if p2_viewed.id == p1.id:
				return True
	return False

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
	if len(name1) < 3 or len(name2) < 3:
		return False
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
		if not school1.start_date and not school1.end_date: continue
		start_date1 = school1.start_date if school1.start_date else datetime.date(1900,1,1)
		end_date1 = school1.end_date if school1.end_date else datetime.date.today()
		for school2 in p2.schools:
			if not school2.name: continue
			if school1.school_linkedin_id and school2.school_linkedin_id: continue
			if not school2.start_date and not school2.end_date: continue
			start_date2 = school2.start_date if school2.start_date else datetime.date(1900,1,1)
			end_date2 = school2.end_date if school2.end_date else datetime.date.today()
			dates_overlap= (start_date1 <= start_date2 <= end_date1) or (start_date2 <= start_date1 <= end_date2)
			# import pdb
			# pdb.set_trace()
			if not dates_overlap: continue
			if name_match(school1.name, school2.name, intersect_threshold=intersect_threshold):
				print uu(school1.name + "-->" + school2.name)
				if len(school2.name) < len(school1.name): return school2.name
				return school1.name
	return None

def has_common_company_names(p1, p2, intersect_threshold=3):
	for job1 in p1.jobs:
		if not job1.company or not job1.company.name: continue
		if not job1.start_date and not job1.end_date: continue
		start_date1 = job1.start_date if job1.start_date else datetime.date(1900,1,1)
		end_date1 = job1.end_date if job1.end_date else datetime.date.today()
		for job2 in p2.jobs:
			if not job2.company or not job2.company.name: continue
			if job1.company_linkedin_id and job2.company_linkedin_id: continue
			if not job2.start_date and not job2.end_date: continue
			start_date2 = job2.start_date if job2.start_date else datetime.date(1900,1,1)
			end_date2 = job2.end_date if job2.end_date else datetime.date.today()
			dates_overlap= (start_date1 <= start_date2 <= end_date1) or (start_date2 <= start_date1 <= end_date2)
			if not dates_overlap: continue
			if name_match(job2.company.name, job1.company.name, intersect_threshold=intersect_threshold):
				print uu(job2.company.name + "-->" + job1.company.name)
				if len(job2.company.name) < len(job1.company.name): return job2.company.name
				return job1.company.name
	return None

def common_school_ids(p1, p2):
	matching = set()
	for school1 in p1.schools:
		if not school1.school_linkedin_id: continue
		if not school1.start_date and not school1.end_date: continue
		start_date1 = school1.start_date if school1.start_date else datetime.date(1900,1,1)
		end_date1 = school1.end_date if school1.end_date else datetime.date.today()
		for school2 in p2.schools:
			if not school2.school_linkedin_id: continue
			if not school2.start_date and not school2.end_date: continue
			start_date2 = school2.start_date if school2.start_date else datetime.date(1900,1,1)
			end_date2 = school2.end_date if school2.end_date else datetime.date.today()
			dates_overlap= (start_date1 <= start_date2 <= end_date1) or (start_date2 <= start_date1 <= end_date2)
			# import pdb
			# pdb.set_trace()
			if not dates_overlap: continue
			if school1.school_linkedin_id == school2.school_linkedin_id:
				matching.add(school2.school_linkedin_id)
	return matching

def common_company_ids(p1, p2):
	matching = set()
	for job1 in p1.jobs:
		if not job1.company_linkedin_id: continue
		if not job1.start_date and not job1.end_date: continue
		start_date1 = job1.start_date if job1.start_date else datetime.date(1900,1,1)
		end_date1 = job1.end_date if job1.end_date else datetime.date.today()
		for job2 in p2.jobs:
			if not job2.company_linkedin_id: continue
			if not job2.start_date and not job2.end_date: continue
			start_date2 = job2.start_date if job2.start_date else datetime.date(1900,1,1)
			end_date2 = job2.end_date if job2.end_date else datetime.date.today()
			dates_overlap= (start_date1 <= start_date2 <= end_date1) or (start_date2 <= start_date1 <= end_date2)
			# import pdb
			# pdb.set_trace()
			if not dates_overlap: continue
			if job1.company_linkedin_id == job2.company_linkedin_id:
				matching.add(job2.company_linkedin_id)
	return matching

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
	if not url:
		return None
	from prime.prospects.models import Prospect, ProspectUrl
	prospectUrl = session.query(ProspectUrl).get(url)
	if prospectUrl:
		prospect = session.query(Prospect).order_by(desc(Prospect.updated)).filter_by(linkedin_id=prospectUrl.linkedin_id).first()
		if prospect: return prospect
	if url.find("https:") ==0:
		url_new = url.replace("https:","http:")
	elif url.find("http:") ==0:
		url_new = url.replace("http:","https:")
	else:
		return None
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
