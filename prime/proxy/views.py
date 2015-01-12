from flask import Flask
import urllib
from flask import render_template, request, jsonify

from . import proxy
from prime.prospects.models import Prospect, Job, Education, Company, School
from prime.prospects.prospect_list import ProspectList
from prime import db

from consume.convert import clean_url
from consume.convert import parse_html
from consume.consumer import create_prospect_from_info as new_prospect
from linkedin.scraper import process_request

session = db.session


@proxy.route("/proxy", methods=['GET', 'POST'])
def proxy():
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        content = process_request(url)
        processed = parse_html(content.get("content"))
        linkedin_id = processed.get("linkedin_id")
        prospect = session.query(Prospect).filter_by(linkedin_id=linkedin_id).first()
        if not prospect:
            prospect = new_prospect(processed, url.replace("https",
                "http"))

        return jsonify({"prospect_url": prospect.url})
