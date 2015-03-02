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
import time, re, os

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')
session = db.session

def process_schools(entity_filter=None):
	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/schools.txt", delimiter='\t')
	if entity_filter!=None:
		df = df[df["id"]==entity_filter]

	#iterate over schools
	for index, row in df.iterrows():
		process_school(row)
		print row["id"]
		
def process_school(row):
	id=row["id"]
	'''
	name=row["name"]
	k = Key(bucket)
	prefix = "/entities/schools/" + str(id) + "/"
	k.key = prefix + "name"
	k.set_contents_from_string(name)		
	'''
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
		df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
		k = Key(bucket)
		k.key = get_file_path(school_id=school_id)
		k.set_contents_from_filename(str(os.getpid())+"temp.csv")		
	
	for by_degree in degrees_dict.items():
		degree = by_degree[0]
		prospects = by_degree[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_degree"] = 1
			df["weight_school_id_degree"] = 1/len(prospects)
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, degree=degree)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")	

	for by_year in years_dict.items():
		year = by_year[0]
		prospects = by_year[1]
		if len(prospects)>0:
			weight = 1/len(prospects)
			df = pandas.DataFrame.from_records({"prospect_id":prospects})
			df["same_school_id_year"] = 1
			df["weight_school_id_year"] = 1/len(prospects)
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, year=year)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")	
		
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
			df.to_csv(path_or_buf=str(os.getpid())+"temp.csv", index=False)
			k = Key(bucket)
			k.key = get_file_path(school_id=school_id, year=year, degree=degree)
			k.set_contents_from_filename(str(os.getpid())+"temp.csv")				

def process_prospects():
	location_dict = defaultdict(int)
	industry_dict = defaultdict(int)
	lines = 0
	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/prospects.txt",  delimiter='\t', chunksize= 100000)
	for chunk in df:
		for index, row in chunk.iterrows():
			location = row["location_raw"]
			industry = row["industry_raw"]
			location_dict[location] += 1			
			industry_dict[industry] += 1	
			lines += 1

	joblib.dump(location_dict, "temp.txt")
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.set_contents_from_filename("temp.txt")	

	joblib.dump(industry_dict, "temp.txt")
	k = Key(bucket)
	k.key = "/entities/industries/counts.dict" 
	k.set_contents_from_filename("temp.txt")		

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
