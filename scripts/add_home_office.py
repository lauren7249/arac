import pandas

import pandas
import requests
import lxml.html
import re
import os
from prime.users.models import User
from prime.managers.models import ManagerProfile
from prime.prospects.models import get_or_create
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
try:
    app = create_app(os.getenv('AC_CONFIG', 'development'))
    db = SQLAlchemy(app)
    session = db.session
except Exception, e:
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
    exception_str = traceback.format_exception(*exc_info)
    if not exception_str: exception_str=[""]    
    print "ERROR: " + str(e)
    print "ERROR: " + "".join(exception_str)
    from prime import db
    session = db.session

df = pandas.read_csv('data/home_office.csv', header=None, delimiter="\t")
df = df.drop_duplicates()

df.columns = ["first_name","last_name","email","phone","address","certifications"]
df = df.fillna("")

for index, row in df.iterrows():
    json_data = {}
    first_name = row.first_name
    last_name = row.last_name
    email = row.email
    username = email.split("@")[0]
    json_data["phone"] = row.phone
    json_data["address"] = row.address
    json_data["certifications"] = row.certifications
    u2 = session.query(User).filter_by(email=email).first()
    if not u2:
        u2 = User(first_name, last_name, email, username)
    session.add(u2)
    mp = ManagerProfile()
    mp.user = u2
    mp.name_suffix = json_data.get("name_suffix")
    mp.certifications = json_data.get("certifications")
    mp.address = json_data.get("address")
    mp.phone = json_data.get("phone")
    session.add(mp)
    session.commit()    
    