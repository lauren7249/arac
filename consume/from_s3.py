from eventlet import *
patcher.monkey_patch(all=True)

import os, sys, time
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket

import logging

logging.basicConfig(filename="s3_download.log", level=logging.INFO)

AWS_KEY = os.environ.get("AWS_KEY")
AWS_SECRET = os.environ.get("AWS_SECRET")
BUCKET = os.environ.get("S3_BUCKET")


def download_file(key_name):
    conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = Bucket(connection=conn, name=BUCKET)
    key = bucket.get_key(key_name)

    try:
        res = key.get_contents_to_filename("data/{}".format(key.name))
    except:
        logging.info(key.name+":"+"FAILED")

if __name__ == "__main__":

    bucket_list = open("list.txt", "r")

    logging.info("Creating a pool")
    pool = GreenPool(size=20)

    logging.info("Saving files in bucket...")
    for key in bucket_list.readlines():
        key = key.strip().replace("\n", "").replace('/', '')
        pool.spawn_n(download_file, key)
    pool.waitall()
