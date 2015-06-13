from boto.s3.key import Key
import boto, os, gzip, re

s3conn = boto.connect_s3(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
bucket = s3conn.get_bucket('51fcd542546078584587d40ec7187804ac_angels')

counts = []
for key in bucket.list("enigma/data/export"):
	dsn = key.key.split("/")[-1]
	key.get_contents_to_filename("key.gz")
	inF = gzip.open("key.gz", 'rb')
	outF = open("key", 'wb')
	outF.write( inF.read() )
	inF.close()
	outF.close()
	num_lines = sum(1 for line in open('key'))
	count = (dsn, num_lines)
	counts.append(count)

outF = open("enigma_data_export_counts.txt", 'ab')
for rec in counts:
	dsn, count = rec
	dsn = re.sub(r".gz$","",dsn)
	dsn = re.sub(r"^com.","",dsn)
	dsn = re.sub(r"\."," ",dsn)
	outF.write(dsn + "\t" + str(count) + "\n")

outF.close()

count = 0
for key in bucket.list("angel_data"):
	count +=1