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
    q.push(json.dumps(data), filter_seen=False, filter_failed=False, filter_working=False)

def get_q():
    redis_url = os.getenv('LINKED_FRIEND_REDIS_URL')
    return RedisQueue('linkedin-assistant', instance_id, redis=get_redis(redis_url))

def main(username, password, prospect_id):
    q = get_q()
    push_to_rq(q, {
        "username": username,
        "password": password,
        "prospect_id": prospect_id
    })

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')

    args = parser.parse_args()
    main(args.username, args.password, args.prospect_id)


