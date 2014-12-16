import logging
import os
import json
import time
import boto
import argparse
from datetime import datetime
from time import sleep

from redis_queue import RedisQueue, get_redis

from consume import process_from_file, upgrade_from_file

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

instance_id = boto.utils.get_instance_metadata()['local-hostname']

def get_q():
    redis_url = os.getenv('CONSUMER_REDIS_URL')
    return RedisQueue('consumer', instance_id, redis=get_redis(redis_url))

def consume_q(q, args):
    real_args = json.loads(args)
    process_from_file(**real_args)

def consume_upgrade_q(q, args):
    real_args = json.loads(args)
    upgrade_from_file(**real_args)

def run_q():
    q = get_q()

    # grab the next piece of work
    while True:
        args = q.pop_block()

        try:
            consume_q(q, args)
        except Exception:
            logger.exception('Exception while processing {}'.format(args))
            q.fail(args)
        else:
            logger.debug('Successfully processed {}'.format(args))
            q.succeed(args)

def run_upgrade_q():
    q = get_q()

    # grab the next piece of work
    while True:
        args = q.pop_block()
        print "upgrading Q"

        try:
            consume_upgrade_q(q, args)
        except Exception:
            logger.exception('Exception while processing {}'.format(args))
            q.fail(args)
        else:
            logger.debug('Successfully processed {}'.format(args))
            q.succeed(args)

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def chunks(number, chunk):
    i = 0
    while i < number:
        i += chunk
        yield i

def upload_file_to_redis(url_file):
    file_length = file_len(url_file)
    old_i = 0
    for i in chunks(file_length, 10000):
        queue_range(url_file, old_i, i)
        old_i = i

def queue_range(url_file, start, end):
    q = get_q()

    print "pushing", url_file, start, end
    q.push(json.dumps({
        'url_file': url_file,
        'start':    start,
        'end':      end
    }))

def retry_all():
    q = get_q()

    q.unfail_all()
    q.unwork_all()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--queue-range', action='store_true')
    parser.add_argument('--retry-all', action='store_true')
    parser.add_argument('--upgrade-all', action='store_true')
    parser.add_argument('--url-file')
    parser.add_argument('--start', type=int)
    parser.add_argument('--end', type=int)
    parser.add_argument('--range', action='store_true')

    args = parser.parse_args()

    if args.queue_range:
        queue_range(args.url_file, args.start, args.end, args.range)
    elif args.retry_all:
        retry_all()
    elif args.upgrade_all:
        print "upgrade"
        run_upgrade_q()
    else:
        run_q()

if __name__ == '__main__':
    main()

