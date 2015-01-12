from flask import Flask
import json
import urllib
from flask import render_template, request, jsonify
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from . import proxy
from prime.prospects.models import Prospect, Job, Education, Company, School
from prime.prospects.prospect_list import ProspectList
from prime import db

from consume.convert import clean_url
from consume.convert import parse_html
from consume.consumer import create_prospect_from_info as new_prospect
from linkedin.run_redis_queue_scraper import process_request_q

session = db.session

AWS_ACCESS_KEY_ID='AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET_ACCESS_KEY='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'

@proxy.route("/proxy", methods=['GET', 'POST'])
def proxy():
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        content = process_request(url)
        processed = parse_html(content.get("content"))
        s3_bucket_name = 'arachid-results'
        s3_conn = S3Connection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3_bucket = s3_conn.get_bucket(s3_bucket_name)
        key = Key(s3_bucket)
        key.key = content['url'].replace('/', '')
        key.set_contents_from_string(json.dumps(content))
        linkedin_id = processed.get("linkedin_id")
        prospect = session.query(Prospect).filter_by(linkedin_id=linkedin_id).first()
        if not prospect:
            prospect = new_prospect(processed, url.replace("https",
                "http"))

        return jsonify({"prospect_url": prospect.url})
