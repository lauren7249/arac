import os
import json
import urlparse
import zlib
import base64

from redis import Redis
from rq import Queue, Worker
from rq.decorators import job

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.kinesis.layer1 import KinesisConnection

from scraper import process_request

kinesis_stream = os.getenv('KINESIS_STREAM')
if not kinesis_stream:
    raise RuntimeError('KINESIS_STREAM must be defined to run the redis scraper')

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError('REDIS_URL must be defined to run the redis scraper')

s3_bucket_name = os.getenv('S3_BUCKET')
if not s3_bucket_name:
    raise RuntimeError('S3_BUCKET  must be defined to run the redis scraper')

urlparse.uses_netloc.append('redis')
url = urlparse.urlparse(redis_url)
redis_conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

s3_conn	   = S3Connection()
s3_bucket  = s3_conn.get_bucket(s3_bucket_name)
kinesis_conn = KinesisConnection()

@job('arachnid_linkedin', connection = redis_conn)
def process_request_job(url):
    # process the url
    results = process_request(url)

    # upload to new key on s3
    kinesis_results = json.dumps({
	'url': results['url'],
	'links': results['links']
    })

    key = Key(s3_bucket)
    key.key = results['url'].replace('/', '-')
    key.set_contents_from_string(json.dumps(results))

    # get the kinesis connection and push the data through
    kinesis_conn.put_record(kinesis_stream, kinesis_results, '0')

if __name__ == '__main__':
    q = Queue('arachnid_linkedin', connection=redis_conn)
    w = Worker(q, connection=redis_conn)
    w.work()
