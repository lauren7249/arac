import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	
from prime import db
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.normalization import *
from datetime import date
import time, re

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
		k = Key(bucket)
		prefix = "/entities/schools/" + str(row["id"]) + "/"

		'''
		for key in bucket.list(prefix=prefix):
		    key.delete()	'''	
		k.key = prefix + "name"
		k.set_contents_from_string(str(row["name"]))		

		#iterate over transactions
		#dict where key is year+degree, value is dict of prospect ids
		degrees_dict = {}
		educations = session.query(Education).filter_by(school_id=row["id"]).all()
		for education in educations:
			prospect_id = education.prospect_id
			school_id = education.school_id
			start_date = education.start_date
			end_date = education.end_date
			degree = education.degree

			if degree is None: degree=""
			degree = normalized_degree(degree)

			if degrees_dict.has_key(degree):
				years_dict = degrees_dict.get(degree)
			else:
				years_dict = {}

			if end_date==None: end_date=date.today()
			if start_date==None: start_date=end_date.replace(year = end_date.year - 4)			

			for year in xrange(start_date.year, end_date.year+1):
				if years_dict.has_key(year):
					prospects = years_dict.get(year)
				else:
					prospects = []
				prospects.append(prospect_id)
				years_dict.update({year:prospects})
			
			degrees_dict.update({degree:years_dict})

		for by_degree in degrees_dict.items():
			degree = by_degree[0]
			years_dict = by_degree[1]
			for by_year in years_dict.items():
				year = by_year[0]
				prospects = by_year[1]
				summary = degree + ", " + str(year) + ": " + str(len(prospects))
				print summary
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

		bucket.copy_key("by_prospect_id/" + str(id) + "/processed_school_id_" + str(school_id) + ".csv", 
			bucket, "entities/schools/" + str(school_id) + "/all.csv")
		bucket.copy_key("by_prospect_id/" + str(id) + "/processed_school_id_" + str(school_id) + "_degree_" + degree, bucket, 
			"entities/schools/" + str(school_id) + "/degree_" + degree + ".csv")

		for year in xrange(start_date.year, end_date.year+1):
			bucket.copy_key("by_prospect_id/" + str(id) + "/processed_school_id_" + str(school_id) + "_year_" + year + ".csv", 
				bucket, "entities/schools/" + str(school_id) + "/year_" + year +  ".csv")
			bucket.copy_key("by_prospect_id/" + str(id) + "/processed_school_id_" + str(school_id) + "_year_" + year + "_degree_" + degree, bucket, 
				"entities/schools/" + str(school_id) + "/year_" + year + "_degree_" + degree + ".csv")
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
