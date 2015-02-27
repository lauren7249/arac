import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	
from prime import db
from prime.prospects.models import Prospect, Job, Education
from datetime import date
import time

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')
session = db.session

def process_schools(entity_filter=None):
	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/schools.txt", delimiter='\t')
	if entity_filter!=None:
			df = df[df["id"]==entity_filter]
	for index, row in df.iterrows():
		k = Key(bucket)
		k.key = "/entities/schools/" + str(row["id"]) + "/name"
		k.set_contents_from_string(str(row["name"]))		
		#make dicts of all prospect ids 
		#prospects = session.execute(ENTITY_SQL % (row["id"]))
		educations = session.query(Education).filter_by(school_id=row["id"]).all()

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

		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 4)
		print start_date
		print end_date

	for job in jobs:
		company_id = job.company_id
		start_date = job.start_date
		end_date = job.end_date
		title = job.title
		start_date=None
		if end_date==None: end_date=date.today()
		if start_date==None: start_date=end_date.replace(year = end_date.year - 2)

		print start_date 
		print end_date

def print_locations():
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.get_contents_to_filename("tmp.txt")	
	mydict = joblib.load("tmp.txt")
	print mydict

if __name__ == "__main__":
	process_entity("schools", 5525527)