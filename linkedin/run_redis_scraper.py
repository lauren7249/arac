import os
import logging
import json
import time
import argparse
from datetime import datetime

from rq import Queue, Worker
from rq.decorators import job

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from get_redis import get_redis
from scraper import process_request

from url_db import UrlDB

logger = logging.getLogger(__name__)


redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError('REDIS_URL must be defined to run the redis scraper')

s3_bucket_name = os.getenv('S3_BUCKET')
if not s3_bucket_name:
    raise RuntimeError('S3_BUCKET  must be defined to run the redis scraper')

redis = get_redis()

url_db = UrlDB(redis)

s3_conn    = S3Connection()
s3_bucket  = s3_conn.get_bucket(s3_bucket_name)

@job('arachnid_linkedin', connection = redis, timeout=15)
def process_request_job(url):
    # check if this url has been procesed
    logger.info("Check Redis")
    if url_db.is_url_finished(url):
        return

    # process the url
    #time.sleep(2)
    logger.info("Processing URL")
    results = process_request(url)
    results['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # get the result links and create jobs from
    # them if they are not finished
    for link in results['links']:
        logger.info("Check Redis Again")
        if not url_db.is_url_finished(link):
            logger.info("New Job")
            process_request_job.delay(link)

    # upload the results to s3
    logger.info("Saving to s3")
    key = Key(s3_bucket)
    key.key = results['url'].replace('/', '')
    key.set_contents_from_string(json.dumps(results))

    logger.info("Mark as finished in Redis")
    url_db.mark_url_finished(url)
    logger.info("Done")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, default=0)

    args = parser.parse_args()
    if args.delay:
        time.sleep(delay)

    q = Queue('arachnid_linkedin', connection=redis)
    w = Worker(q, connection=redis)
    w.work()

if __name__ == '__main__':
    main()

