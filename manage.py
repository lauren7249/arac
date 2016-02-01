#!/usr/bin/env python
import os
import json
from flask.ext.migrate import MigrateCommand, Migrate
from flask.ext.script import Manager, Shell
import re
from prime import create_app, db
from prime.prospects.views import get_q

app = create_app(os.getenv('AC_CONFIG', 'default'))
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
        from_linkedin = set()
        from_gmail = set()
        from_yahoo = set()
        from_windowslive = set()
        from_aol = set()
        from_all = set()
        account_sources = {}
        for record in contacts_array:
            owner = record.get("contacts_owner")              
            if owner:
                account_email = owner.get("email",[{}])[0].get("address","").lower()   
            else: 
                account_email = 'linkedin'                    
            service = record.get("service","").lower()
            account_sources[account_email] = service
            contact = record.get("contact",{})
            emails = contact.get("email",[{}])
            try:
                email_address = emails[0].get("address",'').lower()
            except Exception, e:
                email_address = ''
                print emails
            if not email_address:
                continue   
            from_all.add(email_address)  
            if service=='linkedin':
                from_linkedin.add(email_address)
            elif service=='gmail':
                from_gmail.add(email_address)
            elif service=='yahoo':
                from_yahoo.add(email_address)
            elif service=='windowslive':
                from_windowslive.add(email_address)
            elif service=='aol':
                from_aol.add(email_address)       
        user.unique_contacts_uploaded = len(from_all)
        user.contacts_from_linkedin = len(from_linkedin)
        user.contacts_from_gmail = len(from_gmail)
        user.contacts_from_yahoo = len(from_yahoo)
        user.contacts_from_windowslive = len(from_windowslive)
        user.contacts_from_aol = len(from_aol)
        user.account_sources = account_sources
        user._statistics = None
        for client_prospect in user.client_prospects:
            session.delete(client_prospect)
        session.add(user)
        session.commit()        
        client_data = {"first_name":user.first_name,"last_name":user.last_name,\
                "email":user.email,"location":user.location,"url":user.linkedin_url,\
                "to_email":user.manager.user.email, "hired": (hired == "True")}
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

    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()

