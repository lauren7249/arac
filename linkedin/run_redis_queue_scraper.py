import logging
import os
import json
from datetime import datetime

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from redis_queue import RedisQueue

from scraper import process_request

logger = logging.getLogger('scraper')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

s3_bucket_name = os.getenv('S3_BUCKET')
if not s3_bucket_name:
    raise RuntimeError('S3_BUCKET  must be defined to run the redis scraper')

s3_conn    = S3Connection()
s3_bucket  = s3_conn.get_bucket(s3_bucket_name)
instance_id = boto.utils.get_instance_metadata()['local-hostname']

def process_request_q(q, url):
    logger.debug('processing url {}'.format(url))
    results = process_request(url)

    results['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # get the result links and create jobs from
    # them if they are not finished
    for link in results['links']:
        logger.debug('pushing url {}'.format(link))
        q.push(link)

    # upload the results to s3
    logger.debug('uploading results for {} to s3'.format(url))
    key = Key(s3_bucket)
    key.key = results['url'].replace('/', '')
    key.set_contents_from_string(json.dumps(results))

    # succeed
    logger.debug('succesfully processed {}'.format(url))
    q.succeed(url)

def main():
    q = RedisQueue('linkedin', instance_id)

    # grab the next piece of work
    while True:
        url = q.pop_block()

        try:
            process_request_q(q, url)
        except Exception as ex:
            q.fail(url)
            logger.exception('Exception while processing {}'.format(url))
            raise ex
        else:
            q.succeed(url)

        url = q.pop_block()

if __name__ == '__main__':
    main()
