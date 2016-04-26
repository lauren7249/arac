import json
import sys
import os
from prime.utils.email import sendgrid_email
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import not_

app = create_app(os.getenv('AC_CONFIG', 'testing'))
db = SQLAlchemy(app)
session = db.session

if __name__=="__main__":
	from prime.users.models import User, ClientProspect
	from prime.managers.models import ManagerProfile
	agents = session.query(User).filter( \
			User.email.contains("@"), not_(User.email.contains("@advisorconnect.co")), \
            User.manager_id != 2, User.manager_id != 8, User.manager_id != 10, \
            User.p200_completed==True, User.p200_submitted_to_manager==False, User.intro_js_seen==False)
	for agent in agents:
		manager = session.query(ManagerProfile).get(agent.manager_id)
		manager_email = manager.user.email
		if manager_email.find("@advisorconnect.co") > -1 or manager_email=="recruitertest@newyorklife.com":
			continue
		available = agent.prospects.count()
		added = agent.p200_count
		skipped = agent.prospects.filter(ClientProspect.processed==True).count()
		if available==0 or skipped>0 or added>0:
			continue
		print "agent:{}, available:{}, added:{}, skipped:{}, manager:{}".format(agent.email, available, added, skipped, manager_email)