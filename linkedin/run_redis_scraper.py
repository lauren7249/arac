import os
import json
import urlparse
from datetime import datetime

from redis import Redis
from rq import Queue, Worker
from rq.decorators import job

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from scraper import process_request

from url_db import UrlDB

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError('REDIS_URL must be defined to run the redis scraper')

s3_bucket_name = os.getenv('S3_BUCKET')
if not s3_bucket_name:
    raise RuntimeError('S3_BUCKET  must be defined to run the redis scraper')

urlparse.uses_netloc.append('redis')
redis_url_parsed = urlparse.urlparse(redis_url)
redis = Redis(
    host=redis_url_parsed.hostname,
    port=redis_url_parsed.port, 
    db=0, 
    password=redis_url_parsed.password
)

url_db = UrlDB(redis)

s3_conn	   = S3Connection()
s3_bucket  = s3_conn.get_bucket(s3_bucket_name)

@job('arachnid_linkedin', connection = redis)
def process_request_job(url):
    # check if this url has been procesed
    if url_db.is_url_finished(url):
	return

    # process the url
    results = process_request(url)
    results['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # get the result links and create jobs from 
    # them if they are not finished
    for link in results['links']:
	if not url_db.is_url_finished(link):
	    process_request_job.delay(link)

    # upload the results to s3
    key = Key(s3_bucket)
    key.key = results['url'].replace('/', '')
    key.set_contents_from_string(json.dumps(results))

    url_db.mark_url_finished(url)

if __name__ == '__main__':
    q = Queue('arachnid_linkedin', connection=redis)
    w = Worker(q, connection=redis)
    w.work()
