from .mrjob_convert2 import *
from boto.s3.connection import S3Connection
import subprocess, sys, os
from boto.s3.key import Key
from sklearn.externals import joblib
from prime.prospects import models
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
from mrjob.emr import EMRJobRunner

s3_dict_name = "processed/linkedin_id_2_prospect_id.dict"
local_dict_name = "linkedin_id_2_prospect_id.dict"
def runner(file_list, num_instances):

	conn = S3Connection(os.environ['AWS_ACCESS_KEY_ID'],os.environ['AWS_SECRET_ACCESS_KEY'])
	bucket = conn.get_bucket('advisorconnect-bigfiles')

	keylookup = bucket.lookup(s3_dict_name)
	keysize = keylookup.size
	print keysize
	if keysize < 200:
		app = Flask(__name__)
		app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
		db = SQLAlchemy(app)
		session = db.session
		linkedin_id_2_prospect_id = dict(session.query(models.Prospect.linkedin_id).add_column(models.Prospect.id).filter(models.Prospect.linkedin_id!=None).all())
		joblib.dump(linkedin_id_2_prospect_id, local_dict_name)
		key = Key(bucket)
		key.key = s3_dict_name
		key.set_contents_from_filename(local_dict_name)
		os.remove(local_dict_name)

	proc = subprocess.Popen(["wc", "-l", file_list], stdout=subprocess.PIPE).communicate()[0]
	total_parts =  int(proc.split(" ")[0])

	try:
		#cancel existing uploads
		uploads = bucket.get_all_multipart_uploads()
		for upload in uploads:
			upload.cancel_upload()
	except:
		print "error canceling multipart uploads - maybe none were there?"
		pass

	educations_mp = bucket.initiate_multipart_upload('processed/educations.txt')
	jobs_mp = bucket.initiate_multipart_upload('processed/jobs.txt')
	prospects_mp = bucket.initiate_multipart_upload('processed/prospects.txt')

	try:
		#mr_job = processLinkedIn(args=[file_list])
		mr_job = processLinkedIn(args=['-r', 'emr', '--num-ec2-instances',str(num_instances), file_list])
		with mr_job.make_runner() as runner:
		    runner.run()					
	except RuntimeError as e:
		print e
		pass 

	# if len(educations_mp.get_all_parts()) == total_parts or True:
	# 	educations_mp.complete_upload()
	# 	print "processed educations file successfully"
	# else:
	# 	educations_mp.cancel_upload()
	# 	print "FAILED on educations file"	

	# if len(jobs_mp.get_all_parts()) == total_parts or True:
	# 	jobs_mp.complete_upload()
	# 	print "processed jobs file successfully"
	# else:
	# 	jobs_mp.cancel_upload()
	# 	print "FAILED on jobs file"	

	# if len(prospects_mp.get_all_parts()) == total_parts or True:
	# 	prospects_mp.complete_upload()
	# 	print "processed prospects file successfully"
	# else:
	# 	prospects_mp.cancel_upload()
	# 	print "FAILED on prospects file"	

def start_job(filename, num_processes):

	#append line number 
	subprocess.call("cat -n '" + filename + "' > '" + filename + "_numbered'", shell=True)

	proc = subprocess.Popen(["wc", "-l", filename + "_numbered"], stdout=subprocess.PIPE).communicate()[0]
	total_parts =  int(proc.split(" ")[0])

	#how many lines do we want to give to each process
	n_lines = (total_parts/num_processes)+1
	
	#create a folder for chunked files
	subprocess.call("rm -r " + filename + "_numbered_dir", shell=True)
	os.makedirs(filename + "_numbered_dir")

	#how many digits we need in the filename subject
	suffix_length = len(str(num_processes + 1))

	#split the file
	subprocess.call("split -d -a " + str(suffix_length) + " -l " + str(n_lines) + " " + filename + "_numbered " + filename + "_numbered_dir/f", shell=True)
	#create a list of filenames
	subprocess.call("ls " + filename + "_numbered_dir > " + filename + "_list", shell=True)
	#sync to s3
	subprocess.call("aws s3 sync " + filename + "_numbered_dir" + " s3://mrjob-lists", shell=True)
	
	#run with the list
	runner(filename + "_list", num_processes+1)

#nohup time python2.6 -m arachnid.consume.run_mrjob_convert finished_oct30 995 > run_mrjob_convert.log
#nohup time python2.6 -m arachnid.consume.run_mrjob_convert arachnid/names 1 > run_mrjob_convert.log
if __name__=="__main__":

	filename = sys.argv[1]
	num_processes = int(sys.argv[2])
	start_job(filename, num_processes)
	

	