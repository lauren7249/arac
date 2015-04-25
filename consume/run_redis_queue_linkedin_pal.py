import logging
import os
import json
import time
import boto
import argparse
from datetime import datetime
from time import sleep

from redis_queue import RedisQueue, get_redis

from linkedin_friend import *

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

instance_id = boto.utils.get_instance_metadata()['local-hostname']

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

if __name__ == '__main__':
    run_q()

