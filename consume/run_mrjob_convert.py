from .mrjob_convert import *
from boto.s3.connection import S3Connection

def runner(urls_path):

	with open(urls_path, 'rb') as fh:
		for line in fh:
			pass
	last = line

	total_parts = int(last.split("\t")[0])

	print "about to process " + str(total_parts) + " linkedin profiles"

	conn = S3Connection("AKIAIWG5K3XHEMEN3MNA", "luf+RyH15uxfq05BlI9xsx8NBeerRB2yrxLyVFJd")
	bucket = conn.get_bucket('advisorconnect-bigfiles')

	try:
		#cancel existing uploads
		uploads = bucket.get_all_multipart_uploads()
		for upload in uploads:
			upload.cancel_upload()
	except:
		print "error canceling multipart uploads - maybe none were there?"
		pass

	# educations_mp = bucket.initiate_multipart_upload('processed/educations.txt')
	# jobs_mp = bucket.initiate_multipart_upload('processed/jobs.txt')
	# prospects_mp = bucket.initiate_multipart_upload('processed/prospects.txt')

	try:
		#mr_job = processLinkedIn(args=[urls_path])
		mr_job = processLinkedIn(args=['-r', 'emr', urls_path])
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

if __name__=="__main__":
	#cat -n "arachnid/names.txt" > "arachnid/names_numbered.txt"
	#python -m arachnid.consume.run_mrjob_convert > run_mrjob_convert.log
	runner('/home/ubuntu/arachnid/names_numbered.txt')
