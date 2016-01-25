#!/usr/bin/env python
import os
import json
from flask.ext.migrate import MigrateCommand, Migrate
from flask.ext.script import Manager, Shell

from prime import create_app, db
from prime.prospects.views import get_q

app = create_app(os.getenv('AC_CONFIG', 'default'))
#app.debug=True

migrate = Migrate(app, db)
if __name__ == '__main__':
    manager = Manager(app)

    @manager.command
    def generate_fake():
        from prime.users.models import db, User
        from prime.managers.models import ManagerProfile
        session = db.session
        u = User('Test', 'Person', 'jamesjohnson11@gmail.com', '123123123')
        session.add(u)
        u2 = User('Test', 'Manager', 'laurentracytalbot@gmail.com', '123123123')
        session.add(u2)
        mp = ManagerProfile()
        mp.user = u2
        mp.users.append(u)
        session.add(mp)
        session.commit()

    @manager.command
    def add_manager(first_name, last_name, email, password, json_data):
        from prime.users.models import db, User
        from prime.managers.models import ManagerProfile
        session = db.session
        u2 = User(first_name, last_name, email, password)
        session.add(u2)
        json_data = json.loads(json_data)
        mp = ManagerProfile()
        mp.user = u2
        mp.name_suffix = json_data.get("name_suffix")
        mp.certifications = json_data.get("certifications")
        mp.address = json_data.get("address")
        mp.phone = json_data.get("phone")
        session.add(mp)
        session.commit()

    @manager.command
    def add_user(first_name, last_name, email, password, location, url, manager_id):
        from prime.users.models import db, User
        session = db.session
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(first_name, last_name, email, password)
        u.manager_id = int(manager_id)
        u.linkedin_location = location
        u.linkedin_url = url
        session.add(u)
        session.commit()

    @manager.command
    def rerun_contacts(email, hired):
        from prime.users.models import db, User
        from prime.prospects.views import queue_processing_service
        from prime.processing_service.saved_request import UserRequest
        from redis import Redis
        from rq import Queue
        session = db.session
        user = User.query.filter_by(email=email).first()
        user_request = UserRequest(email)
        contacts_array = user_request.lookup_data()
        n_linkedin = 0
        n_gmail = 0
        n_yahoo = 0
        n_windowslive = 0
        n_contacts = 0
        account_sources = {}
        for record in contacts_array:
            n_contacts+=1
            owner = record.get("contacts_owner")              
            if owner:
                account_email = owner.get("email",[{}])[0].get("address","").lower()   
            else: 
                account_email = 'linkedin'                    
            service = record.get("service","").lower()
            account_sources[account_email] = service
            if service=='linkedin':
                n_linkedin+=1
            elif service=='gmail':
                n_gmail+=1
            elif service=='yahoo':
                n_yahoo+=1
            elif service=='windowslive':
                n_windowslive+=1                
        user.unique_contacts_uploaded = n_contacts
        user.contacts_from_linkedin = n_linkedin
        user.contacts_from_gmail = n_gmail
        user.contacts_from_yahoo = n_yahoo
        user.contacts_from_windowslive = n_windowslive
        user.account_sources = account_sources
        user._statistics = None
        for client_prospect in user.client_prospects:
            session.delete(client_prospect)
        session.add(user)
        session.commit()        
        client_data = {"first_name":user.first_name,"last_name":user.last_name,\
                "email":user.email,"location":user.linkedin_location,"url":user.linkedin_url,\
                "to_email":user.manager.user.email, "hired": (hired == "True")}
        q = get_q()
        q.enqueue(queue_processing_service, client_data, contacts_array, timeout=14400)

    @manager.command
    def delete_prospects(email):
        from prime.users.models import db, User
        user = User.query.filter_by(email=email).first()
        session = db.session
        prospects = user.client_prospects
        for p in prospects:
            session.delete(p)
        session.commit()
        print str(len(prospects)) + " client prospects deleted "

    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()

