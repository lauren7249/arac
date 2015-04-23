from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
import re, os, sys
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.prospect_list import *
from consume.consumer import *
from prime import create_app, db

def get_session():
	app = Flask(__name__)
	app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
	db = SQLAlchemy(app)
	session = db.session
	return session

session = get_session()

def from_linkedin_id(linkedin_id):
	#session = get_session()
	prospect = session.query(Prospect).filter_by(linkedin_id=str(linkedin_id)).first()
	return prospect

def from_url(url):
	#session = get_session()
	url = re.sub("https:","http:",url)
	prospect = session.query(Prospect).filter_by(s3_key=url.replace("/", "")).first()
	return prospect

def from_prospect_id(id):
	#session = get_session()
	prospect = session.query(Prospect).get(id)
	return prospect


def update_network(url):
	prospect = update_prospect_from_url(url)
	p = ProspectList(prospect)
	plist = p.get_results()

	for d in plist:
		update_prospect_from_url(d.get("url"))

if __name__=="__main__":
	url = sys.argv[1]
	update_network(url)