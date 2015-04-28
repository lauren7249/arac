import logging
import os
import json
import boto.utils
import argparse

from redis_queue import RedisQueue, get_redis

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

def main():
    q = get_q()
    q.unwork_all()

if __name__ == '__main__':
    main()


