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

df = pandas.read_csv('data/managers.csv', header=None)
df = df.drop_duplicates()
managers = list(df[0].values)

redo = []
for manager in managers:
    email = manager.lower().strip()
    username = email.split("@")[0]
    link = "http://www.newyorklife.com/recruiter/" + username
    request = requests.get(link, allow_redirects=True)
    page = lxml.html.fromstring(request.content)
    try:
        full_name = page.find(".//figcaption/h3").text_content()
    except:
        link = "http://www.newyorklife.com/agent/" + username
        request = requests.get(link, allow_redirects=True)
        page = lxml.html.fromstring(request.content)   
        try:
            full_name = page.find(".//figcaption/h3").text_content()
        except:     
            redo.append(email)
            continue        
    json_data = {}
    first_name = full_name.split(" ")[0].strip().capitalize()
    last_name = ""
    for chunk in full_name.split(" ")[1:]:
        last_name += chunk.strip().capitalize() + " "
    last_name = last_name.strip()
    print first_name
    print last_name
    print email    
    position = page.find(".//figcaption/p[@class='position']").text_content()
    if position.find("|") > -1:
        certifications = position.split("|")[0].strip()
        json_data["certifications"] = re.sub("[^A-Za-z\.\(\)\-]+",", ", certifications)
    location = page.find(".//figcaption/ul/li[@class='location']").text_content()
    location = re.sub("\s"," ", location)
    location = re.sub("\xa0","\n",location)
    location = re.sub("Map\xbb$","",location.strip())
    location = re.sub("( ){2,}","", location)
    address_line2 = re.search(",\s+[A-Z\s]+,\s+[A-Z]{2}\s+[0-9]{5}\-[0-9]{4}",location).group(0)
    address_line1 = location.replace(address_line2,"")
    address_line1 = re.sub("\s"," ", address_line1).strip()
    address_line2 = re.sub("\s"," ", address_line2).strip()
    address_line1 = re.sub(",$","", address_line1)
    address_line2 = re.sub(",$","", address_line2)
    address_line1 = re.sub("^,","", address_line1)
    address_line2 = re.sub("^,","", address_line2)    
    json_data["address"] = address_line1.strip() + "\n" + address_line2.strip()
    try:
        phone = page.find(".//figcaption/ul/li[@class='phone']").text_content().strip()
        json_data["phone"] = re.sub("[^0-9 \(\)\-]+",", ", phone)
    except:
        pass
    print json_data
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

print "\n".join(redo)