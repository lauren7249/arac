import logging
import os
import subprocess
import signal
import json
import time
import boto.utils
import boto.ec2
import argparse
from datetime import datetime
from time import sleep

from prime.prospects import models
from prime.users.models import User
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config

from redis_queue import RedisQueue, get_redis

from linkedin_friend import *
import sys

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

instance_id = boto.utils.get_instance_metadata()['local-hostname']

try:
    app = create_app(os.getenv('AC_CONFIG', 'beta'))
    db = SQLAlchemy(app)
    session = db.session
except:
    from prime import db
    session = db.session

def push_to_rq(q, data):
    q.push(json.dumps(data))

def get_q():
    redis_url = os.getenv('LINKED_FRIEND_REDIS_URL')
    return RedisQueue('linkedin-assistant', instance_id, redis=get_redis(redis_url))

def kill_firefox_and_xvfb():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for i, line in enumerate(out.splitlines()):
        if i > 0:
            if 'firefox' in line or 'xvfb' in line.lower():
                print line
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)
                print "killed"


def consume_q(q, args):
    print "started q"
    '''
    expected args:
        username
        password
    '''
    real_args = json.loads(args)
    print args
    print real_args

    print "init firefox"
    pal = LinkedinFriend(**real_args)
    print "login started"
    pal.login()
    print "login done"
    linkedin_id = pal.linkedin_id
    print "connects started"
    connects = pal.get_first_degree_connections()
    print "connects done"
    pal.shutdown()
    print "firefox shutdown"
    user_id = real_args.get("user_id")
    user = session.query(User).filter(User.user_id == int(user_id)).first()
    user_json = user.json if user.json else {}
    user_json['boosted_ids'] = connects
    session.query(User).filter(User.user_id == int(user_id)).update({
        "json":user_json,
        "linkedin_id": linkedin_id
        })
    session.commit()
    connects = None
    print connects

def run_q():
    q = get_q()

    # grab the next piece of work
    while True:
        logger.debug('Dequeueing data from Redis')
        args = q.pop_block(tries=3)

        if args is None:
            logger.debug('Nothing on RedisQueue')
            continue

        try:
            consume_q(q, args)
        except Exception:
            logger.exception('Exception while processing {}'.format(args))
            q.fail(args)
        else:
            logger.debug('Successfully processed {}'.format(args))
            q.succeed(args)
        break

def shutdown():
    # Either shutdown instance or exit script.
    sys.exit(1)

def doAwesomeStuff(q, args):
    try:
        consume_q(q, args)
    except Exception:
        logger.exception('Exception while processing {}'.format(args))
        kill_firefox_and_xvfb()
        q.fail(args)
    else:
        logger.debug('Successfully processed {}'.format(args))
        q.succeed(args)

def worker(irish):

    q = get_q()

    # Constantly get jobs from RedisQueue
    # If there is a job, then do awesome stuff.
    # Otherwise, shutdown (unless 'IRISH_CAB' is True)
    while True:
        # Step 1: Get data from Q
        logger.debug('Dequeueing data from Redis')
        args = q.pop_block(tries=3)
        if args is None:
            logger.debug('Nothing on RedisQueue')
            if irish:
                continue
            else:
                shutdown()
        else:
            print args, "args found"
            doAwesomeStuff(q, args)

def master():

    workerQuota = 100
    tagKey = "worker-group"
    tagFilter = "tag:" + tagFilter
    tagVal = '1'

    # AWS Connect
    REGION = 'us-east-1'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    conn = boto.ec2.connect_to_region(REGION,
                                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    # AWS Launch Instance
    AMI_IMAGE_ID = 'ami-924043fa'
    KEY_NAME = 'processing'
    INSTANCE_TYPE = 'm1.small'
    SECURITY_GROUPS = ['scrapers']

    q = get_q()

    # Constantly check if there are enough instances running to handle jobs in RedisQueue.
    # If there are too many jobs, run a new instance.
    while True:
        # Step 1: Measure Q for Data
        logger.debug('Fetching RedisQueue Stats')
        stats = q.get_stats()
        pending = stats.pending

        # Step 2: Check AWS for Instances.
        reservations = c.get_all_instances(filters={tagFilter:workerGroup})
        averageJobs = pending / len(reservations)
        logger.debug('There are {} workers, and {} pending jobs. \
            Average jobs per worker is {}'.format(len(reservations), pending, averageJobs))

        # Step 2a: If not enough Instances, then create more Instances.
        if averageJobs > workerQuota:
            logger.debug('Average Jobs per worker exceeded quota. Launching new worker.')
            reservation = conn.run_instances(
                AMI_IMAGE_ID,
                key_name=KEY_NAME,
                instance_type=INSTANCE_TYPE,
                security_groups=SECURITY_GROUPS)
            for instance in reservation.instances:
                logger.debug('Tagging {} with {}:{}'.format(instanced.id, tagKey, tagVal))
                instance.add_tag(tagKey, tagVal)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('purpose')
    parser.add_argument('--irish', action='store_true')
    args = parser.parse_args()

    purpose = args.purpose
    irish = args.irish

    if purpose == 'master':
        master()
    elif purpose == 'worker':
        worker(irish)
    else:
        print "Use a valid purpose: master|worker"
        print "Exiting"
        sys.exit(1)



