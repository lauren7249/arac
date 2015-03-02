from __future__ import division
import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	
from prime import db
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.normalization import *
from prime.prospects.filepaths import * 
from datetime import date
import time, re

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')
session = db.session

def process_schools(school_id, degree=None, year=None):
	prospects = []
	if degree is not None:
		matches_filter = session.query(Education).filter_by(school_id=school_id, degree=degree).all()
		if year is None:
			suffix ="school_id_degree"
		else :
			suffix="school_id_degree_year"
	else :
		matches_filter = session.query(Education).filter_by(school_id=school_id).all()
		if year is None:
			suffix ="school_id"	
		else:
			suffix="school_id_year"	
	'''
	for education in matches_filter:
		prospect_id = education.prospect_id
		if year is None:
			prospects.append(prospect_id)
		else:
			start_date = education.start_date
			end_date = education.end_date
			if end_date==None: end_date=date.today()
			if start_date==None: start_date=end_date.replace(year = end_date.year - 4)
			if year>=start_date.year or year<=end_date.year:
				prospects.append(prospect_id)
	'''
	#weight = 1/len(prospects)
	df = pandas.DataFrame.from_records({"prospect_id":prospects})
	df["same_"+suffix] = 1
	#df["weight_"+suffix] = 1/len(prospects)
	#print df
	return df

def process_prospect(id):
	prospect = session.query(Prospect).get(id)
	educations = prospect.schools
	jobs = prospect.jobs

	dfs = []
	for education in educations:
		school_id = education.school_id
		start_date = education.start_date
		end_date = education.end_date
		degree = education.degree

		#degree = normalized_degree(degree)

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 4)

		if degree is not None and len(degree)>0:
			dfs.append(process_schools(school_id, degree=degree))

		for year in xrange(start_date.year, end_date.year+1):
			dfs.append(process_schools(school_id, year=year))
			if degree is not None and len(degree)>0:
				dfs.append(process_schools(school_id, year=year, degree=degree))
	return dfs
'''
	for job in jobs:
		company_id = job.company_id
		start_date = job.start_date
		end_date = job.end_date
		title = job.title

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 2)

		for year in xrange(start_date.year, end_date.year+1):
			print year

	for prospect_id in prospect_ids:'''

def print_locations():
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.get_contents_to_filename("tmp.txt")	
	mydict = joblib.load("tmp.txt")
	print mydict
