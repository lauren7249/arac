import os
import json

from redis import Redis
from rq import Queue
from rq.decorators import job

from boto.kinesis.layer1 import KinesisConnection

from .scraper import process_request

kinesis_stream = os.getenv('KINESIS_STREAM')
if not kinesis_stream:
    raise RuntimeError('KINESIS_STREAM must be defined to run the redis scraper')

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError('REDIS_URL must be defined to run the redis scraper')

urlparse.uses_netloc.append('redis')
url = urlparse.urlparse(redis_url)
redis_conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

kinesis_conn = KinesisConnection()

@job('linkedin', connection = redis_conn)
def process_request_job(url):
    # process the url
    results = proess_request(url)
    result_str = json.load(results)

    # get the kinesis connection and push the data through
    kinesis_conn.put_record(kinesis_stream, result_str, '0')

if __name__ == '__main__':
    with Connection(conn):
        q = Queue('linkedin', connection=redis_conn)
        w = Worker(q, connection=redis_conn)
        w.work()
