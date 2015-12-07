import logging
import hashlib
import boto
import json
import os
import urlparse
from redis import Redis
import psycopg2
import psycopg2.extras

from flask import redirect, request, url_for, flash, render_template, session \
as flask_session, jsonify
from flask.ext.login import login_user, logout_user, current_user, fresh_login_required

from . import crawlera
from prime import db, csrf
from prime.utils.crawlera import reformat_crawlera


logger = logging.getLogger(__name__)
#TODO get this info into the config
CONNECTION_STRING = "dbname='ac_labs' user='arachnid' host='babel.priv.advisorconnect.co' password='devious8ob8'"

@csrf.exempt
@crawlera.route('/v1/person', methods=['POST'])
def get_person():
    if request.method == 'POST':
        url = request.form.get("url")
        id =  request.form.get("id")
        conn = psycopg2.connect(CONNECTION_STRING)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if url:
            url = url.replace("https://","http://")
            query = """SELECT * from people where url='%s'""" % (url)
        else:
            query = """SELECT * from people where linkedin_id='%s'""" % (linkedin_id)
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            return {}
        row = dict(row)
        output = reformat_crawlera(row)
        return jsonify(output)
    return jsonify({})


