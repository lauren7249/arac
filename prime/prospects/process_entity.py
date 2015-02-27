import pandas, csv
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from collections import defaultdict
from sklearn.externals import joblib	

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')

def process_entity(entity_type):
	df = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/" + entity_type + ".txt", delimiter='\t')
	for index, row in df.iterrows():
		k = Key(bucket)
		k.key = "/entities/" + entity_type + "/" + str(row["id"]) + "/name"
		k.set_contents_from_string(str(row["name"]))		

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

def print_locations():
	k = Key(bucket)
	k.key = "/entities/locations/counts.dict" 
	k.get_contents_to_filename("tmp.txt")	
	mydict = joblib.load("tmp.txt")
	print mydict