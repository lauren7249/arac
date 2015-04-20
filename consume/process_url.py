from consume.consumer import *
import sys
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
import pandas
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
db = SQLAlchemy(app)
session = db.session

url = sys.argv[1]

info1 = get_info_for_url_live(url)
info2 = get_info_for_url(url)
if info1.get("jobs") is None: 
	info = info2
	print "no info from live url"
else: 
	info = info1
print info
prospect = create_prospect_from_info(info, url, _session=session)

