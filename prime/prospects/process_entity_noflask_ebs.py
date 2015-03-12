from __future__ import division
import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.normalization import *
from prime.prospects.filepaths import * 
from datetime import datetime
import time, re, os
import urllib2
import os, math, numpy
from prime import create_app, db

from prime.prospects import models
import os
from flask.ext.sqlalchemy import SQLAlchemy

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')

def process_schools(entity_filter=None):
	if not os.path.exists('/mnt/big/entities'): os.mkdir('/mnt/big/entities')
	if not os.path.exists('/mnt/big/entities/schools'): os.mkdir('/mnt/big/entities/schools')

	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/schools.txt", delimiter='\t')
	ed = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/educations.txt", delimiter='\t', parse_dates=True)
	ed["start_date"] = pandas.to_datetime(ed['start_date'])
	ed["start_date"] = pandas.DatetimeIndex(ed["start_date"]).year
	ed["end_date"] = pandas.to_datetime(ed['end_date'])
	ed["end_date"] = pandas.DatetimeIndex(ed["end_date"]).year

	ed["end_date"].fillna(datetime.today().year, inplace=True)
	ed["start_date"].fillna(ed["end_date"]-4, inplace=True)
	if entity_filter!=None:
		df = df[df["id"]==entity_filter]

	#iterate over schools
	for index, row in df.iterrows():
		id = row["id"]
		if not os.path.exists('/mnt/big/entities/schools/'+str(id)): os.mkdir('/mnt/big/entities/schools/'+str(id))
		process_school(id, ed)

def process_school(id, educations_df):
	if os.path.exists('/mnt/big/entities/schools/'+str(id) + "/all.csv"): return

	#iterate over transactions
	#dict where key is year+degree, value is dict of prospect ids
	degrees_dict = {}
	years_dict = {}
	degrees_years_dict = {}
	all_prospects = []
	educations = educations_df[educations_df.school_id == id]
	for index, row in educations.iterrows():
		prospect_id = row.prospect_id
		school_id = row.school_id
		start_date = row.start_date
		end_date = row.end_date
		degree = row.degree

		if degree is None: degree=""
		degree = normalized_degree(degree)

		if degrees_dict.has_key(degree):
			prospects_in_degree = degrees_dict.get(degree)
		else:
			prospects_in_degree = []
		prospects_in_degree.append(prospect_id)
		degrees_dict.update({degree:prospects_in_degree})
		all_prospects.append(prospect_id)

		for year in xrange(int(start_date), int(end_date)+1):
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
	
	for by_degree in degrees_dict.items():
		degree = by_degree[0]
		prospects = by_degree[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_degree"] = 1
			df["weight_school_id_degree"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, degree=degree), index=False)

	for by_year in years_dict.items():
		year = by_year[0]
		prospects = by_year[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_year"] = 1
			df["weight_school_id_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, year=year), index=False)
		
	for by_year_degree in degrees_years_dict.items():
		year_degree = by_year_degree[0]
		year = year_degree[0]
		degree = year_degree[1]
		prospects = by_year_degree[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_degree_year"] = 1
			df["weight_school_id_degree_year"] = 1/len(prospects)
			df.to_csv(path_or_buf='/mnt/big/' + get_file_path(school_id=school_id, year=year, degree=degree), index=False)		
	#print id

def process_company(id):

	try:
		ret = urllib2.urlopen('https://s3.amazonaws.com/advisorconnect-bigfiles/entities/companies/' + str(id) + '/all.csv')
		return
	except:
		pass


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
		df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
		k = Key(bucket)
		k.key = get_file_path(company_id=company_id)
		k.set_contents_from_filename(str(os.getpid())+"temp.csv")		
	
	for by_location in locations_dict.items():
		location = by_location[0]
		prospects = by_location[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_company_id_location"] = 1
			df["weight_company_id_location"] = 1/len(prospects)
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, location=location)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")	

	for by_year in years_dict.items():
		year = by_year[0]
		prospects = by_year[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_company_id_year"] = 1
			df["weight_company_id_year"] = 1/len(prospects)
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, year=year)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")	
		
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
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(company_id=company_id, year=year, location=location)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")				
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
			bucket.copy_key(get_file_path(prospect_id=id,school_id=school_id, degree=degree), 'advisorconnect-bigfiles', 
				get_file_path(school_id=school_id, degree=degree))

		for year in xrange(start_date.year, end_date.year+1):
			bucket.copy_key(get_file_path(prospect_id=id,school_id=school_id, year=year), 
				'advisorconnect-bigfiles', get_file_path(school_id=school_id, year=year))
			if degree is not None and len(degree)>0:
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

		if location is not None and len(location)>0:
			bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, location=location), 'advisorconnect-bigfiles', 
				get_file_path(company_id=company_id, location=location))

		for year in xrange(start_date.year, end_date.year+1):
			bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, year=year), 
				'advisorconnect-bigfiles', get_file_path(company_id=company_id, year=year))
			if location is not None and len(location)>0:
				bucket.copy_key(get_file_path(prospect_id=id,company_id=company_id, location=location, year=year), 'advisorconnect-bigfiles', 
					get_file_path(company_id=company_id, location=location, year=year))
def print_locations():
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.get_contents_to_filename("tmp.txt")	
	mydict = joblib.load("tmp.txt")
	print mydict

if __name__ == "__main__":
	process_schools()