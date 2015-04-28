import logging
import os
import json
import time
import boto.utils
import argparse
from datetime import datetime
from time import sleep

from redis_queue import RedisQueue, get_redis

from linkedin_friend import *
import sys

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

instance_id = boto.utils.get_instance_metadata()['local-hostname']

def push_to_rq(q, data):
    q.push(json.dumps(data))

def get_q():
    redis_url = os.getenv('LINKED_FRIEND_REDIS_URL')
    return RedisQueue('linkedin-assistant', instance_id, redis=get_redis(redis_url))

def consume_q(q, args):
    real_args = json.loads(args)
    pal = LinkedinFriend(**real_args)
    pal.login()
    linkedin_id = pal.linkedin_id
    connects = pal.get_first_degree_connections()
    print connects

def run_q():
    logger.debug('Getting RedisQ')
    q = get_q()
    q.unwork_all()
    logger.debug('Got RedisQ')

    push_to_rq(q, { 'url': 'https://linkedin.com' })
    print q.get_stats()

    # grab the next piece of work
    while True:
        logger.debug('Getting Message From Q')
        args = q.pop_block(tries=3)
        logger.debug('Got Message From Q')
        print args
        break

        try:
            consume_q(q, args)
        except Exception:
            logger.exception('Exception while processing {}'.format(args))
            q.fail(args)
        else:
            logger.debug('Successfully processed {}'.format(args))
            q.succeed(args)
        break

if __name__ == '__main__':
    run_q()


