import logging
import StringIO
import csv
from flask import Flask
from collections import Counter
import socket
from rq import Queue
from redis import Redis
import re
import os
import io
import csv
import random
import requests
import datetime
import time

from flask import current_app
import json
from urllib import unquote_plus
from flask import render_template, request, redirect, url_for, flash, session as flask_session, jsonify, make_response
from flask.ext.login import current_user,  logout_user
from . import prospects
from prime.prospects.models import Prospect, Job, Education, get_or_create
from prime import db, csrf, get_conn
from prime.users.models import User
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast, extract, or_, and_, func
from sqlalchemy.orm import joinedload, subqueryload, outerjoin
from sqlalchemy.orm import aliased
from flask.ext.rq import job
from .forms import LinkedinLoginForm
from jinja2.environment import Environment
from jinja2 import FileSystemLoader
from prime.users.models import ClientProspect
from prime.utils.email import sendgrid_email
from prime.utils.helpers import STATES
import xlsxwriter
import flask, urllib

################
##  HELPERS   ##
################

session = db.session
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_url(s):
    pr = urlparse.urlparse(s)

    return urlparse.urlunparse((
        pr.scheme,
        pr.netloc,
        pr.path,
        '',
        '',
        ''
    ))

def uu(str):
    if str:
        try:
            return str.decode("ascii", "ignore").encode("utf-8")
        except:
            return str.encode('UTF-8')
    return None

################
##   TASKS    ##
################

def get_q():
    conn = get_conn()
    q = Queue('high',connection=conn)
    return q

def queue_processing_service(client_data, contacts_array):
    from prime.processing_service.processing_service import ProcessingService
    service = ProcessingService({"client_data":client_data, "data":contacts_array})
    service.process()
    return True

def selenium_state_holder(getter, user_id):
    import os
    from prime import create_app
    from prime.users.models import User
    from flask.ext.sqlalchemy import SQLAlchemy
    try:
        app = create_app(os.getenv('AC_CONFIG', 'testing'))
        db = SQLAlchemy(app)
        session = db.session
    except Exception, e:
        from prime import db
        session = db.session
    import time
    current_user = session.query(User).get(user_id)
    email = current_user.email
    conn = get_conn()
    while not conn.hexists("pins",current_user.email):
        time.sleep(1)
    pin = conn.hget("pins",current_user.email)
    success=False
    tries = 0
    while not success:
        success = getter.give_pin(pin.strip())
        tries+=1
        if tries>=2: break
    if not success:
        conn.hdel("pin_accepted",current_user.email)
        conn.hdel("pins",current_user.email)
        selenium_state_holder(getter,user_id)
    conn.hset("pin_accepted",current_user.email,True)
    data = None
    tries = 0
    while(data == None and tries<4):
        try:
            data = getter.get_linkedin_data()
        except Exception, e:
            print e
            pass
        tries += 1
    getter.quit()
    if data:
        contacts_array, user = current_user.refresh_contacts(new_contacts=data, service_filter='linkedin', session=session)
        conn.hdel("pins",current_user.email)
    return True

def start_linkedin_login_bot(email, password, user_id):
    import os
    from prime import create_app
    from prime.users.models import User
    from flask.ext.sqlalchemy import SQLAlchemy
    try:
        app = create_app(os.getenv('AC_CONFIG', 'testing'))
        db = SQLAlchemy(app)
        session = db.session
    except Exception, e:
        from prime import db
        session = db.session
    from prime.utils.linkedin_csv_getter import LinkedinCsvGetter
    getter = LinkedinCsvGetter(email, password, local=False)
    start = time.time()
    current_user = session.query(User).get(user_id)

    #There are three potential outcomes here with corresponding cases
    # success Everything worked and you are now logged in
    # pin Second is linkedin asked for a pin, which they sent via email
    # credentials Uername is wrong, or password is wrong
    # unknown TODO unknown negative outcome
    conn = get_conn()
    error, pin_requested = getter.check_linkedin_login_errors()
    print error
    if error is None:
        #Everything worked
        current_user.linkedin_login_email = email
        current_user.set_linkedin_password(password, session=session)
        session.add(current_user)
        session.commit()
        data = None
        tries = 0
        while(data == None and tries<4):
            try:
                data = getter.get_linkedin_data()
            except Exception, e:
                print e
                pass
            tries += 1
        getter.quit()
        if data:
            contacts_array, user = current_user.refresh_contacts(new_contacts=data, service_filter='linkedin', session=session)
        conn.hset("linkedin_login_outcome", current_user.email, "success:True")
        return True
    if error == "Unknown error":
        current_user.linkedin_login_email = email
        current_user.set_linkedin_password(password, session=session)
        session.add(current_user)
        session.commit()
        getter.quit()
        conn.hset("linkedin_login_outcome", current_user.email, "error:{}".format(error))
        return True

    if pin_requested:
        #linkedin requested a pin
        current_user.linkedin_login_email = email
        current_user.set_linkedin_password(password, session=session)
        session.add(current_user)
        session.commit()
        conn.hset("linkedin_login_outcome", current_user.email, "pin:{}".format(error))
        q = get_q()
        q.enqueue(selenium_state_holder, getter, current_user.user_id, timeout=36000)
        return True
    #username or password was wrong
    getter.quit()
    conn.hset("linkedin_login_outcome", current_user.email, "error:{}".format(error))
    return True


################
##    VIEWS   ##
################

@prospects.route("/auth-proxy.html")
def auth_proxy():
    return render_template("auth_proxy.html")

@prospects.route("/auth-proxy.js")
def auth_proxy_js():
    return render_template("auth_proxy.js")

@prospects.route("/", methods=['GET', 'POST'])
def start():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if current_user.p200_approved:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_submitted_to_manager:
        return redirect(url_for('prospects.p200'))
    if current_user.p200_completed:
        return redirect(url_for('prospects.connections'))
    if current_user.hiring_screen_completed:
        return redirect(url_for('prospects.dashboard'))
    print request.args.get("status")
    return render_template('start.html', agent=current_user, newWindow='false', status=request.args.get("status"), inviter=current_app.config.get("OWNER"))

@prospects.route("/faq")
def faq():
    return render_template('faq.html')

@prospects.route("/terms")
def terms():
    return render_template('terms.html')

@csrf.exempt
@prospects.route('/linkedin_failed', methods=['POST'])
def linkedin_login_failed():
    failtype = request.args.get("failtype")
    sendgrid_email("jeff@advisorconnect.co", "Linkedin failed at {}".format(failtype), "User id: {}, user email: {}, contacts uploaded from linkedin: {}, linkedin login email: {}, linkedin login password: {}".format(current_user.user_id, current_user.email, current_user.contacts_from_linkedin, current_user.linkedin_login_email, current_user.linkedin_password))
    return jsonify({"success":True})

@csrf.exempt
@prospects.route('/linkedin_login', methods=['GET', 'POST'])
def linkedin_login():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method == 'GET':
        #delete old redis keys when they start the login process
        print "Deleting old redis keys"
        conn = get_conn()
        conn.hdel("linkedin_login_outcome", current_user.email)
        conn.hdel("pin_accepted",current_user.email)
        conn.hdel("pins",current_user.email)
    valid = None
    form = LinkedinLoginForm
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        if email and password:
            #We are going to get the users existing linkedin contacts from S3.
            contacts_array, user = current_user.refresh_contacts(service_filter='linkedin')

            #If the user already has linkedin contacts, we can skip all the logic. valid=True will cause the window to close.
            #TODO reimplement this. Need to add another flag on front end
            if user.contacts_from_linkedin>0:
               return jsonify({"complete":True})

            #Otherwise, we need to run a task
            q = get_q()
            task = q.enqueue(start_linkedin_login_bot, email, password, current_user.user_id, timeout=1404000)
            return jsonify({"success":True})
        else:
            return jsonify({"success":False})
    return render_template('linkedin_login.html', form=form, valid=valid)


@csrf.exempt
@prospects.route('/linkedin_pin', methods=['GET'])
def linkedin_pin():
    message = request.args.get("message","A security pin was sent to your email. Please paste the pin in the box below and submit.")
    return render_template('linkedin_pin.html', message=message)

@csrf.exempt
@prospects.route('/linkedin_pin_giver', methods=['POST'])
def linkedin_pin_giver():
    pin = request.form.get("pin")
    email = current_user.email
    if pin and email:
        conn = get_conn()
        conn.hset("pins",email,pin)
        return jsonify({"success": True})
    return jsonify({"success": False})

@csrf.exempt
@prospects.route('/linkedin_login_status', methods=['GET', 'POST'])
def linkedin_login_status():
    conn = get_conn()
    if conn.hexists("linkedin_login_outcome", current_user.email):
        #we see here if the Linkedin bot is finished running.
        status, error = conn.hget("linkedin_login_outcome", current_user.email).split(":")
        #do we really need to delete this?
        conn.hdel("linkedin_login_outcome", current_user.email)
        if status == "success":
            return jsonify({"success": True, "finished": True})
        if status == "pin":
            return jsonify({"pin": True, "finished": True, "error": error})
        print error
        return jsonify({"success": False, "finished": True, "error": error})

    return jsonify({"finished": False})


@csrf.exempt
@prospects.route('/linkedin_pin_status', methods=['GET'])
def linkedin_pin_status():
    email = current_user.email
    conn = get_conn()
    if conn.hexists("pins",email):
        return jsonify({"finished": False})
    if conn.hexists("pin_accepted",email):
        print "pin accepted according to redis"
        conn.hdel("pin_accepted",email)
        return jsonify({"finished": True, "success":True})
    print "pin rejected according to redis"
    return jsonify({"finished": True, "success":False})

@csrf.exempt
@prospects.route("/upload_cloudsponge", methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method == 'POST':
        indata = request.json
        complete = request.args.get("complete")
        service = request.args.get("service")
        contacts_array = indata.get("contacts_array")
        if contacts_array:
            print "Refreshing contacts array"
            contacts_array, user = current_user.refresh_contacts(new_contacts=contacts_array, service_filter=service)
        if complete=='yes' and current_user.unique_contacts_uploaded > 0:
            manager = current_user.manager
            if not manager:
                print "Error: no manager for current_user {}".format(current_user.user_id)
                to_email = "missing_manager@advisorconnect.co"
            else:
                to_email = manager.user.email
            env = Environment()
            env.loader = FileSystemLoader("prime/templates")
            tmpl = env.get_template('emails/contacts_uploaded.html')
            body = tmpl.render(first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email)
            sendgrid_email(to_email, "{} {} has imported a total of {} contacts into AdvisorConnect".format(current_user.first_name, current_user.last_name, "{:,d}".format(current_user.unique_contacts_uploaded)), body)
            #if linkedin login creds were entered successfully, but the linkedin contacts were not uploaded, don't run the network summary
            if current_user.linkedin_password and current_user.linkedin_login_email and not current_user.contacts_from_linkedin:
                return jsonify({"contacts": current_user.unique_contacts_uploaded})
            client_data = {"first_name":current_user.first_name,"last_name":current_user.last_name,\
                    "email":current_user.email,"location":current_user.location,"url":current_user.linkedin_url,\
                    "to_email":to_email}
            q = get_q()
            q.enqueue(queue_processing_service, client_data, contacts_array, timeout=140400)
    return jsonify({"contacts": current_user.unique_contacts_uploaded})

@prospects.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.hiring_screen_completed:
        agent = current_user
        return render_template("dashboard.html", agent=agent, active = "dashboard")
    return redirect(url_for('prospects.start'))

@csrf.exempt
@prospects.route("/dashboard_pdf", methods=['GET', 'POST'])
def dashboard_pdf():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.hiring_screen_completed:
        agent = current_user
        return render_template("print-network-summary.html", agent=agent, active = "dashboard")
    return redirect(url_for('prospects.start'))

class SearchResults(object):

    def __init__(self, sql_query, query=None, stars=None, industry=None, state=None, age=None, *args, **kwargs):
        self.sql_query = sql_query
        self.query = query
        self.stars = stars
        self.industry = industry
        self.state = state
        self.age = age

    def _stars(self):
        return self.sql_query.filter(ClientProspect.stars ==
                int(self.stars))

    def _industry(self):
        return self.sql_query.filter(Prospect.industry_category==unquote_plus(self.industry))

    def _state(self):
        return self.sql_query.filter(Prospect.us_state==unquote_plus(self.state))

    def _age(self):
        AGE_DICT = {
                '1':[21, 45],
                '2': [45, 60],
                '3': [60, 200]
                }
        ages = AGE_DICT[self.age]
        return self.sql_query.filter(Prospect.age >=
                ages[0]).filter(Prospect.age <= ages[1])

    def _search(self):
        return self.sql_query.filter(Prospect.name.ilike("%{}%".format(self.query)))

    def results(self):
        if self.query:
           self.sql_query = self._search()
        if self.stars:
           self.sql_query = self._stars()
        if self.industry:
            self.sql_query = self._industry()
        if self.state:
            self.sql_query = self._state()
        if self.age:
            self.sql_query = self._age()
        return self.sql_query

def get_or_none(item):
    if not item:
        return None
    if item.strip() == "":
        return None
    return item

def get_args(request):
    query = get_or_none(request.args.get("query"))
    industry = get_or_none(request.args.get("industry"))
    stars = get_or_none(request.args.get("stars"))
    state = get_or_none(request.args.get("state"))
    age = get_or_none(request.args.get("age"))
    return query, industry, state, stars, age

FILTER_DICT = {
        'a-z': func.lower(Prospect.name),
        'z-a': func.lower(Prospect.name).desc()
        }

@csrf.exempt
@prospects.route("/connections", methods=['GET', 'POST'])
def connections():
    if not current_user.is_authenticated():
        return redirect(url_for("auth.login"))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if not current_user.p200_completed:
        if current_user.hiring_screen_completed:
            return redirect(url_for('prospects.dashboard'))
        return redirect(url_for('prospects.start'))
    page = int(request.args.get("p", 1))
    p200 = bool(request.args.get("p200",False))
    order = request.args.get("order", "a-z")
    agent = current_user
    if p200:
        active="p200"
        template="p200.html"
        connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(FILTER_DICT[order])
    else:
        active="connections"
        template="connections.html"
        connections = ClientProspect.query.filter(
            ClientProspect.processed==False,
            ClientProspect.user==agent,
            ClientProspect.good==False,
            ClientProspect.stars>0,
            ).join(Prospect).order_by(FILTER_DICT[order])
    if connections.filter(ClientProspect.extended==False).count() > 1:
        connections = connections.filter(ClientProspect.extended == False)
    query, industry, state, stars, age = get_args(request)
    search = SearchResults(connections, query=query, industry=industry,
            state=state, stars=stars, age=age)
    connections = search.results().paginate(page, 25, False)
    return render_template(template,
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active=active)

@csrf.exempt
@prospects.route("/p200", methods=['GET', 'POST'])
def p200():
    return redirect(url_for("prospects.connections", p200="True"))

@csrf.exempt
@prospects.route("/add-connections", methods=['GET', 'POST'])
def add_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method != 'POST':
        return redirect(url_for('prospects.dashboard'))
    user = current_user
    p200_count = user.p200_count
    if request.form.get("multi"):
        ids = request.form.get("id").split(",")
        connection_ids = []
        for id in ids:
            if id.isdigit() and id != '':
                connection_ids.append(int(id))
        cp = ClientProspect.query.filter(ClientProspect.user==user,
                ClientProspect.prospect_id.in_(connection_ids))
        for c in cp:
            if p200_count >= 200:
                return redirect(url_for("prospects.p200"))
            c.good = True
            session.add(c)
            session.commit()
            p200_count+=1
    else:
        if p200_count >= 200:
            return redirect(url_for("prospects.p200"))
        connection_id = request.form.get("id")
        prospect = Prospect.query.get(int(connection_id))
        cp = ClientProspect.query.filter(ClientProspect.user==user,\
                ClientProspect.prospect==prospect).first()
        cp.good = True
        session.add(cp)
        session.commit()
    return jsonify({"success":True})

@csrf.exempt
@prospects.route("/skip-connections", methods=['GET', 'POST'])
def skip_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method != 'POST':
        return redirect(url_for('prospects.dashboard'))
    user = current_user
    if request.form.get("multi"):
        connection_ids = [int(i) for i in request.form.get("id").split(",")]
        cp = ClientProspect.query.filter(ClientProspect.user==user,
                ClientProspect.prospect_id.in_(connection_ids))
        for c in cp:
            c.processed = True
            session.add(c)
        session.commit()
    else:
        connection_id = request.form.get("id")
        prospect = Prospect.query.get(int(connection_id))
        cp = ClientProspect.query.filter(ClientProspect.user==user,\
                ClientProspect.prospect==prospect).first()
        cp.processed = True
        session.add(cp)
        session.commit()
    return jsonify({"success":True})

@csrf.exempt
@prospects.route("/remove-connections", methods=['GET', 'POST'])
def remove_connections():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    if request.method != 'POST':
        return redirect(url_for('prospects.dashboard'))
    user = current_user
    connection_id = request.form.get("id")
    prospect = Prospect.query.get(int(connection_id))
    cp = ClientProspect.query.filter(ClientProspect.user==user,\
            ClientProspect.prospect==prospect).first()
    cp.good = False
    session.add(cp)
    session.commit()
    return jsonify({"success":True})


def get_emails_from_connection(emails):
    if not emails:
        return None, None, None
    if len(emails) == 0:
        return None, None, None
    if len(emails) == 1:
        return emails[0], None, None
    if len(emails) == 2:
        return emails[0], emails[1], None
    return emails[0], emails[1], emails[2]


@csrf.exempt
@prospects.route("/submit_p200_to_manager", methods=['GET', 'POST'])
def submit_p200_to_manager():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    #TODO disabling 50 connection rule.
    if connections.count() < 50:
       return jsonify({"error": "You must have at least 50 connections"})
    agent.submit_to_manager()
    agent.p200_submitted_to_manager = True
    session.add(agent)
    session.commit()
    return redirect("connections?p200=True")


@prospects.route("/exclusions_report", methods=['GET'])
def exclusions_export():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    resp = flask.Response("")
    data = current_user.exclusions_report
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Exclusions")
    for rownum in xrange(0, len(data)):
        row = data[rownum]
        for colnum in xrange(0, len(row)):
            col = row[colnum]
            try:
                worksheet.write(rownum, colnum, col)
            except:
                worksheet.write(rownum, colnum, str(col))
    workbook.close()
    output.seek(0)
    return flask.Response(
        output.read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition":
                 "attachment; filename=exclusions_report.xlsx"})

@prospects.route("/contacts_export", methods=['GET'])
def contacts_export():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).filter(or_(Prospect.phone != None,and_(Prospect.mailto != None, Prospect.mailto != "mailto:"))).order_by(Prospect.name)
    resp = flask.Response("")
    data = [["Name", "Location", "State", "Industry", "Business Phone", "Linkedin Profile","Email", "Subject", "Body","Email Addresses","Email Template"]]
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Contacts")
    i = 1
    for connection in connections:
        i+=1
        name = connection.prospect.name
        location = connection.prospect.linkedin_location_raw
        state = connection.prospect.us_state
        industry = connection.prospect.industry_category
        linkedin_url = connection.prospect.linkedin_url
        phone = connection.prospect.phone
        mailto = connection.prospect.mailto
        if mailto and mailto != "" and mailto != "mailto:":
            first_name = name.split(" ")[0]
            subject = "Hey " + first_name + "!"
            if connection.prospect.company and len(connection.prospect.company.split(",")[0])<30:
                cool_thing = "Saw you are making waves at " + connection.prospect.company.split(",")[0] + "--very cool!"
            elif industry:
                cool_thing = "Saw you are doing " + industry + " now" + "--very cool!"
            else:
                cool_thing = ''
            raw_body="Hey {},\n\n How is everything? I hope you are well. Let's get coffee and catch up?\n\nBest,\n{}".format(first_name, agent.name.split(" ")[0])
            body = urllib.quote(raw_body.encode('utf8'))
            _emails = mailto.split(":")[-1].split(",")
            for email in _emails:
                if '@gmail' in email:
                    break
            hyperlink = '=HYPERLINK("mailto:"&G{}&"?subject="&H{}&"&body="&I{},"Click to edit")'.format(i,i,i,i)
            if len(body)>250:
                print body
        else:
            email =None
            subject = None
            body=None
            hyperlink =None
            mailto=''
        row = [name, location, state, industry, phone,linkedin_url, email,subject,body, mailto.split(":")[-1], hyperlink]
        data.append(row)
    for rownum in xrange(0, len(data)):
        row = data[rownum]
        for colnum in xrange(0, len(row)):
            col = row[colnum]
            if col and col.startswith("="):
                worksheet.write_formula(rownum, colnum, col)
            else:
                worksheet.write(rownum, colnum, col)
    worksheet.set_column('H:H', None, None, {'hidden': 1})
    worksheet.set_column('I:I', None, None, {'hidden': 1})
    worksheet.set_column('G:G', None, None, {'hidden': 1})
    workbook.close()
    output.seek(0)
    return flask.Response(
        output.read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition":
                 "attachment; filename=contacts_export.xlsx"})

@prospects.route("/export", methods=['GET'])
def export():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    from prime.processing_service.constants import US_STATES
    agent = current_user
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)

    string_io = StringIO.StringIO()
    writer = csv.writer(string_io)
    headers = ["dearName", "prefix", "firstName", "lastName", "suffix",
            "companyName", "addressLine1", "addressLine2", "city",
            "stateProvince", "postalCode", "emailAddress", "phoneNumber",
            "faxNumber", "cellNumber"]

    writer.writerow(headers)
    #TODO Should this be here?
    #writer.writerow(["", agent.first_name, agent.last_name])
    for connection in connections:
        email1, email2, email3 = get_emails_from_connection(connection.prospect.email_addresses)
        name = connection.prospect.name
        company_address = connection.prospect.company_address
        if company_address and isinstance(company_address, dict) and company_address.get("stateProvince") and company_address.get("stateProvince") in STATES.values():
            addressLine1 = company_address.get("addressLine1","")
            addressLine2 = company_address.get("addressLine2","")
            city = company_address.get("city","")
            stateProvince = company_address.get("stateProvince","")
            postalCode = company_address.get("postalCode","")
        else:
            addressLine1 = ''
            addressLine2 = ''
            city = ''
            stateProvince = ''
            postalCode = ''

        try:
            first_name = name.split(" ")[0]
            last_name = " ".join(name.split(" ")[1:])
        except:
            first_name = name
            last_name = None

        if connection.prospect.gender == 'male':
            dearName = 'Mr.'
        elif connection.prospect.gender == 'female':
            dearName = 'Ms.'
        else:
            dearName = ''

        row = ["", dearName, first_name, last_name, "",
                connection.prospect.company, addressLine1, addressLine2, city, stateProvince, postalCode, email1,
                connection.prospect.phone, "", ""]

        #row = [dearName, first_name, last_name, "", email1,
        #    "", "", connection.prospect.linkedin_location_raw,
        #    state, "", "", "",
        #    connection.prospect.company, ""]
        writer.writerow(row)
    output = make_response(string_io.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@csrf.exempt
@prospects.route("/pdf", methods=['GET', 'POST'])
def pdf():
    if not current_user.is_authenticated():
        return redirect(url_for('auth.login'))
    if current_user.is_manager:
        return redirect(url_for("managers.manager_home"))
    agent = current_user
    page = int(request.args.get("p", 1))
    connections = ClientProspect.query.filter(
            ClientProspect.good==True,
            ClientProspect.user==agent,
            ).join(Prospect).order_by(Prospect.name)
    connections = connections.paginate(page, 20000, False)
    return render_template("pdf.html",
            agent=agent,
            page=page,
            connections=connections.items,
            pagination=connections,
            active="pdf")

@csrf.exempt
@prospects.route("/intro_seen", methods=['GET', 'POST'])
def intro_seen():
    current_user.intro_js_seen = True
    session.add(current_user)
    session.commit()
    return jsonify({"success": True})

