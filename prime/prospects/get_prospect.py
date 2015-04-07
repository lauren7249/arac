from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
import re, os
from prime.prospects.models import Prospect, Job, Education

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
db = SQLAlchemy(app)
session = db.session

def from_linkedin_id(linkedin_id):
	prospect = session.query(Prospect).filter_by(linkedin_id=str(linkedin_id)).first()
	return prospect

def from_url(url):
	url = re.sub("https:","http:",url)
	prospect = session.query(Prospect).filter_by(s3_key=url.replace("/", "")).first()
	return prospect

def from_prospect_id(id):
	prospect = session.query(Prospect).get(id)
	return prospect