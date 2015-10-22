from __future__ import division
import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.normalization import *
from prime.prospects.filepaths import * 
from datetime import date
import time, re, os
import urllib2
import os
from prime import create_app, db
import boto
from prime.prospects import models
import os
from flask.ext.sqlalchemy import SQLAlchemy

boto.config.add_section('Boto')
boto.config.set('Boto','http_socket_timeout','10')

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET, host='s3.amazonaws.com')
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')

session = db.session

def process_schools(entity_filter=None):
	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/schools.txt", delimiter='\t')
	if entity_filter!=None:
		df = df[df["id"]==entity_filter]

	#iterate over schools
	for index, row in df.iterrows():
		process_school(row)

def process_school(id, selected_degree=None, selected_year=None):
	try:
		app = create_app(os.getenv('AC_CONFIG', 'beta'))
		db = SQLAlchemy(app)
		session = db.session
	except:
		from prime import db
		session = db.session

	if not os.path.exists('/mnt/big/entities/schools/'+str(id)): os.mkdir('/mnt/big/entities/schools/'+str(id))		
	'''
	name=row["name"]
	k = Key(bucket)
	prefix = "/entities/schools/" + str(id) + "/"
	k.key = prefix + "name"
	k.set_contents_from_string(name)		
	'''
	print 'school' + str(id)

	#iterate over transactions
	#dict where key is year+degree, value is dict of prospect ids
	degrees_dict = {}
	years_dict = {}
	degrees_years_dict = {}
	all_prospects = []
	educations = session.query(Education).filter_by(school_id=id).all()
	for education in educations:
		prospect_id = education.prospect_id
		school_id = education.school_id
		start_date = education.start_date
		end_date = education.end_date
		degree = education.degree

		if degree is None: degree=""
		degree = normalized_degree(degree)

		if degrees_dict.has_key(degree):
			prospects_in_degree = degrees_dict.get(degree)
		else:
			prospects_in_degree = []
		prospects_in_degree.append(prospect_id)
		degrees_dict.update({degree:prospects_in_degree})
		all_prospects.append(prospect_id)

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 4)			

		for year in xrange(start_date.year, end_date.year+1):
			if years_dict.has_key(year):
				prospects_in_year = years_dict.get(year)
			else:
				prospects_in_year = []
			prospects_in_year.append(prospect_id)
			years_dict.update({year:prospects_in_year})
			if degrees_years_dict.has_key((year,degree)):
				prospects_in_year_degree = degrees_years_dict.get((year,degree))
			else:
				prospects_in_year_degree = []
			prospects_in_year_degree.append(prospect_id)
			degrees_years_dict.update({(year,degree):prospects_in_year_degree})			
	if len(all_prospects)>0:
		df = pandas.DataFrame.from_records({"prospect_id":all_prospects})
		df["same_school_id"] = 1
		df["weight_school_id"] = 1/len(all_prospects)
		df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id), index=False)
		k = Key(bucket)
		k.key = get_file_path(school_id=school_id)
		k.set_contents_from_file(open('/mnt/big/' + get_file_path(school_id=school_id),'r+'))		
	
	for by_degree in degrees_dict.items():
		degree = by_degree[0]
		if selected_degree is not None and degree != selected_degree: continue
		prospects = by_degree[1]
		if len(prospects) and len(degree)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_degree"] = 1
			df["weight_school_id_degree"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, degree=degree), index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, degree=degree)
			k.set_contents_from_file(open('/mnt/big/' + get_file_path(school_id=school_id, degree=degree),'r+'))	

	for by_year in years_dict.items():
		year = by_year[0]
		if selected_year is not None and year != selected_year: continue
		prospects = by_year[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_year"] = 1
			df["weight_school_id_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, year=year), index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, year=year)
			k.set_contents_from_file(open('/mnt/big/' + get_file_path(school_id=school_id, year=year),'r+'))	
		
	for by_year_degree in degrees_years_dict.items():
		year_degree = by_year_degree[0]
		year = year_degree[0]
		degree = year_degree[1]
		if selected_year is not None and year != selected_year: continue
		if selected_degree is not None and degree != selected_degree: continue
		prospects = by_year_degree[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_degree_year"] = 1
			df["weight_school_id_degree_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, degree=degree, year=year), index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, year=year, degree=degree)
			k.set_contents_from_file(open('/mnt/big/' + get_file_path(school_id=school_id, degree=degree, year=year),'r+'))				
	

def process_company(id):
	try:
		app = create_app(os.getenv('AC_CONFIG', 'beta'))
		db = SQLAlchemy(app)
		session = db.session
	except:
		from prime import db
		session = db.session
	#iterate over transactions
	#dict where key is year+location, value is dict of prospect ids
	locations_dict = {}
	years_dict = {}
	locations_years_dict = {}
	all_prospects = []
	jobs = session.query(Job).filter_by(company_id=id).all()
	for job in jobs:
		prospect_id = job.prospect_id
		company_id = job.company_id
		start_date = job.start_date
		end_date = job.end_date
		location = job.location

		if location is None: location=""
		location = normalized_location(location)

		if locations_dict.has_key(location):
			prospects_in_location = locations_dict.get(location)
		else:
			prospects_in_location = []
		prospects_in_location.append(prospect_id)
		locations_dict.update({location:prospects_in_location})
		all_prospects.append(prospect_id)

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 2)			

		for year in xrange(start_date.year, end_date.year+1):
			if years_dict.has_key(year):
				prospects_in_year = years_dict.get(year)
			else:
				prospects_in_year = []
			prospects_in_year.append(prospect_id)
			years_dict.update({year:prospects_in_year})
			if locations_years_dict.has_key((year,location)):
				prospects_in_year_location = locations_years_dict.get((year,location))
			else:
				prospects_in_year_location = []
			prospects_in_year_location.append(prospect_id)
			locations_years_dict.update({(year,location):prospects_in_year_location})			
	if len(all_prospects)>0:
		df = pandas.DataFrame.from_records({"prospect_id":all_prospects})
		df["same_company_id"] = 1
		df["weight_company_id"] = 1/len(all_prospects)
		df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id), index=False)
		k = Key(bucket)
		k.key = get_file_path(company_id=company_id)
		k.set_contents_from_filename('/mnt/big/' + get_file_path(school_id=school_id))		
	
	for by_location in locations_dict.items():
		location = by_location[0]
		prospects = by_location[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_company_id_location"] = 1
			df["weight_company_id_location"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id), index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, location=location)
			k.set_contents_from_filename('/mnt/big/' + get_file_path(school_id=school_id))	

	for by_year in years_dict.items():
		year = by_year[0]
		prospects = by_year[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_company_id_year"] = 1
			df["weight_company_id_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id), index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, year=year)
			k.set_contents_from_filename('/mnt/big/' + get_file_path(school_id=school_id))	
		
	for by_year_location in locations_years_dict.items():
		year_location = by_year_location[0]
		year = year_location[0]
		location = year_location[1]
		prospects = by_year_location[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_company_id_location_year"] = 1
			df["weight_company_id_location_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id), index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, year=year, location=location)
			k.set_contents_from_filename('/mnt/big/' + get_file_path(school_id=school_id))				
	print id	
	
def process_prospect(id):
	prospect = session.query(Prospect).get(id)
	educations = prospect.schools
	jobs = prospect.jobs
	for education in educations:
		school_id = education.school_id
		start_date = education.start_date
		end_date = education.end_date
		degree = education.degree

		degree = normalized_degree(degree)

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 4)

		if degree is not None and len(degree)>0:
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, degree=degree)
			if not k.exists(): process_school(school_id, selected_degree=degree)			
			bucket.copy_key(get_file_path(prospect_id=id,school_id=school_id, degree=degree), 'advisorconnect-bigfiles', 
				get_file_path(school_id=school_id, degree=degree))

		for year in xrange(start_date.year, end_date.year+1):
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, year=year)
			if not k.exists(): process_school(school_id, selected_year=year)				
			bucket.copy_key(get_file_path(prospect_id=id,school_id=school_id, year=year), 
				'advisorconnect-bigfiles', get_file_path(school_id=school_id, year=year))
			if degree is not None and len(degree)>0:
				k = Key(bucket)
				k.key = get_file_path(school_id=school_id, year=year, degree=degree)
				if not k.exists(): process_school(school_id, selected_year=year, selected_degree=degree)				
				bucket.copy_key(get_file_path(prospect_id=id,school_id=school_id, degree=degree, year=year), 'advisorconnect-bigfiles', 
					get_file_path(school_id=school_id, degree=degree, year=year))

	for job in jobs:
		company_id = job.company_id
		start_date = job.start_date
		end_date = job.end_date
		location = job.location

		location = normalized_location(location)

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 2)

		k = Key(bucket)
		k.key = get_file_path(company_id=company_id)
		if not k.exists(): process_company(company_id)

		if location is not None and len(location)>0:
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, location=location)
			if not k.exists(): process_company(company_id)			
			bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, location=location), 'advisorconnect-bigfiles', 
				get_file_path(company_id=company_id, location=location))

		for year in xrange(start_date.year, end_date.year+1):
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, year=year)
			if not k.exists(): process_company(company_id)			
			bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, year=year), 
				'advisorconnect-bigfiles', get_file_path(company_id=company_id, year=year))
			if location is not None and len(location)>0:
				k = Key(bucket)
				k.key = get_file_path(company_id=company_id, year=year, location=location)
				if not k.exists(): process_company(company_id)					
				bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, location=location, year=year), 'advisorconnect-bigfiles', 
					get_file_path(company_id=company_id, location=location, year=year))

def print_locations():
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.get_contents_to_filename("tmp.txt")	
	mydict = joblib.load("tmp.txt")
	print mydict
