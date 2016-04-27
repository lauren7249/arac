#!/usr/bin/env python
import os
import json
from flask.ext.migrate import MigrateCommand, Migrate
from flask.ext.script import Manager, Shell
import re
from prime import create_app, db
from prime.prospects.views import get_q

app = create_app(os.getenv('AC_CONFIG', 'testing'))
#app.debug=True

migrate = Migrate(app, db)
if __name__ == '__main__':
    manager = Manager(app)

    @manager.command
    def add_manager(first_name, last_name, email, password, json_data):
        from prime.users.models import db, User
        from prime.managers.models import ManagerProfile
        email = email.lower()
        session = db.session
        json_data = json.loads(json_data)
        user = User.query.filter(User.email==email).first()
        mp = None
        if not user:
            user = User(first_name, last_name, email, password)
            session.commit()
            session.add(user)  
        else:
            user.set_password(password)            
        mp = ManagerProfile.query.filter(ManagerProfile.user_id==user.user_id).first()
        if not mp:
            mp = ManagerProfile()
        mp.address = json_data.get("address")
        mp.name_suffix = json_data.get("name_suffix")
        mp.certifications = json_data.get("certifications")
        mp.phone = json_data.get("phone")
        mp.job_title = json_data.get("job_title")      
        mp.user = user            
        session.add(mp)
        session.commit()
        print "Manager id: {}".format(mp.manager_id)

    @manager.command
    def add_user(first_name, last_name, email, password, manager_id):
        from prime.users.models import db, User
        email = email.lower()
        session = db.session
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(first_name, last_name, email, password)
        else:
            u.set_password(password)   
        u.manager_id = int(manager_id)
        session.add(u)
        session.commit()
        manager = u.manager
        manager.users.append(u)
        session.add(manager)
        session.commit()

    @manager.command
    def rerun_contacts(email, hired, flush, suppress_emails):
        from prime.users.models import db, User
        from prime.prospects.views import queue_processing_service
        email = email.lower()
        session = db.session
        user = User.query.filter_by(email=email).first()
        contacts_array, user = user.refresh_contacts()
        print len(contacts_array)
        if email == 'jrocchi@ft.newyorklife.com':
            other_locations = ["New York, New York","Boston, MA","Hartford, Connecticut","Washington, DC"]
        else:
            other_locations = []
        client_data = {"first_name":user.first_name,"last_name":user.last_name,\
                "email":user.email,"location":user.location,"url":user.linkedin_url,\
                "to_email":user.manager.user.email, "hired": (hired == "True"),
                "suppress_emails":(suppress_emails == "True"), "other_locations":other_locations}
        print json.dumps(client_data, indent=3)
        if flush=='True':
            print "flushing old data"
            user.clear_data()
            for client_prospect in user.client_prospects:
                session.delete(client_prospect)
            user.p200_completed = False
            user.p200_started = False
            user.hiring_screen_started = False
            user.hiring_screen_completed = False
            user.p200_submitted_to_manager = False
            user.p200_approved = False
            user.hired = False
            user.not_hired = False
            user.not_hired_reason = None
            user._statistics = {}
            user._statistics_p200 = {}
            user.all_states = {}
            user.intro_js_seen = False
            session.add(user)
            session.commit()
        q = get_q()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=14400)

    @manager.command
    def delete_user(email):
        from prime.users.models import db, User
        email = email.lower()
        user = User.query.filter_by(email=email).first()
        session = db.session
        prospects = user.client_prospects
        for p in prospects:
            session.delete(p)
        session.delete(user)
        session.commit()


    @manager.command
    def delete_users(pattern):
        from prime.users.models import db, User
        users = User.query.all()
        for user in users:
            email = user.email.lower()
            if re.search(pattern, email):
                print email
                delete_user(email)

    @manager.command
    def add_csv(email, filename):
        from prime.users.models import User, db
        from prime.prospects.views import queue_processing_service
        from helpers.linkedin_helpers import process_csv
        email = email.lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User('', '', email, '')
        f = open(filename,'rb')
        csv = f.read()
        data = process_csv(csv)
        contacts_array, user = user.refresh_contacts(new_contacts=data, service_filter='linkedin', session=db.session)
        print user.contacts_from_linkedin

    #this replaces add_csv and uses local selenium to download the data when it fails on saucelabs. only run locally
    @manager.command
    def upload_csv(email, linkedin_email, linkedin_password):
        from prime import db
        from prime.users.models import User
        from prime.utils.linkedin_csv_getter import LinkedinCsvGetter
        getter = LinkedinCsvGetter(linkedin_email, linkedin_password, local=True)
        errors = getter.check_linkedin_login_errors()
        data = getter.get_linkedin_data()
        getter.quit()
        email = email.lower()
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User('', '', email, '')
        contacts_array, user = u.refresh_contacts(new_contacts=data, service_filter='linkedin', session=db.session)
        print len(contacts_array)

    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()

