from flask import Flask
import json
import urllib
from flask import render_template, request, jsonify
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from . import proxy
from prime.prospects.models import Prospect, Job, Education, Company, School
from prime.prospects.views import clean_url
from prime.prospects.prospect_list import ProspectList
from prime import db

from consume.convert import clean_url
from consume.convert import parse_html
from consume.consumer import create_prospect_from_info as new_prospect
from linkedin.scraper import process_request

session = db.session

AWS_ACCESS_KEY_ID='AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET_ACCESS_KEY='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'

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@proxy.route("/proxy", methods=['GET', 'POST'])
@crossdomain(origin='*')
def proxy():
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        prospect = session.query(Prospect).filter_by(s3_key=url.replace("https", "http").replace("/", "")).first()
        if prospect:
            print "found prospect"
            return jsonify({"prospect_url": prospect.url})

        content = process_request(url)
        processed = parse_html(content.get("content"))
        """
        s3_bucket_name = 'arachid-results'
        s3_conn = S3Connection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3_bucket = s3_conn.get_bucket(s3_bucket_name)
        key = Key(s3_bucket)
        key.key = content['url'].replace('/', '')
        key.set_contents_from_string(json.dumps(content))
        """
        linkedin_id = processed.get("linkedin_id")
        prospect = session.query(Prospect).filter_by(linkedin_id=linkedin_id).first()
        if not prospect:
            prospect = new_prospect(processed, url.replace("https",
                "http"))

        return jsonify({"prospect_url": prospect.url})
