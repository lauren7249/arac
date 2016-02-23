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
        json_data = json.loads(json_data)
        mp = ManagerProfile()
        mp.address = json_data.get("address")
        mp.name_suffix = json_data.get("name_suffix")
        mp.certifications = json_data.get("certifications")
        mp.phone = json_data.get("phone")
        session = db.session
        user = User(first_name, last_name, email, password)
        session.add(user)
        mp.user = user
        session.add(mp)
        session.commit()
        print "Manager id: {}".format(mp.manager_id)

    @manager.command
    def add_user(first_name, last_name, email, password, manager_id):
        from prime.users.models import db, User
        session = db.session
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(first_name, last_name, email, password)
        u.manager_id = int(manager_id)
        session.add(u)
        session.commit()
        manager = u.manager
        manager.users.append(u)
        session.add(manager)
        session.commit()

    @manager.command
    def rerun_contacts(email, hired, flush):
        from prime.users.models import db, User
        from prime.prospects.views import queue_processing_service
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
                "suppress_emails":True, "other_locations":other_locations}
        print client_data
        if flush=='True':
            user.clear_data()
            for client_prospect in user.client_prospects:
                session.delete(client_prospect)
            user._statistics = None
            session.add(user)
            session.commit()
        q = get_q()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=14400)

    @manager.command
    def delete_user(email):
        from prime.users.models import db, User
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
            email = user.email
            if re.search(pattern, email):
                print email
                delete_user(email)

    @manager.command
    def add_facebook(email, filename):
        import pandas
        from prime.users.models import User
        from prime.prospects.views import queue_processing_service
        user = User.query.filter_by(email=email).first()
        s = pandas.read_csv(filename, header=None)
        s.fillna("", inplace=True)
        data = []
        for index, row in s.iterrows():
            contact = {}
            contact["email"] = [{"address": row[0].strip() + "@facebook.com"}]
            data.append({"contact":contact, "contacts_owner":None, "service":"facebook"})
        client_data = {"first_name":user.first_name,"last_name":user.last_name,\
                "email":user.email,"location":user.location,"url":user.linkedin_url, "hired": True}
        q = get_q()
        q.enqueue(queue_processing_service, client_data, data, timeout=14400)


    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()

