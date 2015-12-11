import os
import datetime
import logging

from flask import current_app
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from sqlalchemy import CheckConstraint
import sqlalchemy.event
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date, \
        Text, Enum, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import SchemaType, TypeDecorator, Enum

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL

from prime import db, login_manager
from prime.prospects.models import Prospect
from prime.customers.models import Customer

logger = logging.getLogger(__name__)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(postgresql.INTEGER, primary_key=True)

    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)
    email = db.Column(String(100), nullable=False, unique=True)
    _password_hash = db.Column('password_hash', String(100), nullable=False)
    is_admin = db.Column(postgresql.BOOLEAN, nullable=False, server_default="FALSE")
    customer_id = db.Column(Integer, ForeignKey("customers.id"))
    customer = relationship('Customer', foreign_keys='User.customer_id')

    linkedin_id = db.Column(String(1024))
    linkedin_url = db.Column(String(1024))
    created = db.Column(Date, default=datetime.datetime.today)

    prospects = db.relationship('Prospect', secondary="client_prospect", \
                               backref=db.backref('prospects', lazy='dynamic'))

    onboarding_code = db.Column(String(40))
    json = db.Column(JSON, default={})

    def __init__(self, first_name, last_name, email, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.first_name = first_name.title()
        self.last_name = last_name.title()
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    @property
    def is_manager(self):
        return len(self.manager_profile) > 0

    def get_id(self):
        return unicode(self.user_id)

    @property
    def generate_reset_token(self):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 3600)
        return s.dumps({'reset': self.user_id})

    @staticmethod
    def reset_password(token, new_password):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 3600)
        try:
            data = s.loads(token)
            u = User.query.get(data.get('reset'))
        except:
            return None
        if u is None:
            return None
        u.password = new_password
        db.session.add(u)
        return u


    @property
    def has_prospects(self):
        session = db.session
        return session.query(ClientProspect).filter(
                ClientProspect.user_id == self.user_id).count() > 0

    @property
    def statistics(self):
        if self.json.get("statistics"):
            return self.json.get("statistics")
        return self.build_statistics()

    def build_statistics(self):
        """
        Complicated function that will calculate most popular schools,
        companies, gender, wealthscore, age, college degree, and income score
        """
        schools = {}
        companies = {}
        male = {True:0,False:0}
        college_degree = {True:0,False:0}
        wealth_score = []
        average_age = []
        for prospect in self.prospects:
            for school in prospect.schools:
                count = schools.get(school.school.name, 0)
                count += 1
                schools[school.school.name] = count
            if len(prospect.schools) == 0:
                college_degree[False] += 1
            else:
                college_degree[True] += 1
            for job in prospect.jobs:
                count = schools.get(job.company.name, 0)
                count += 1
                schools[job.company.name] = count
            average_age.append(prospect.age if prospect.age else 30)
            wealth_score.append(prospect.wealthscore if prospect.wealthscore
                    else 40)
            if prospect.is_male:
                male[True] += 1
            else:
                male[False] += 1
        data = {"schools": schools,
                "companies": companies,
                "male": male[True]/(male[True] + male[False]) * 100,
                "college_degree": college_degree[True]/(college_degree[True] + college_degree[False]) * 100,
                "average_age": sum(average_age)/len(average_age),
                "wealth_score": sum(wealth_score)/len(wealth_score)}
        old_json = self.json if self.json else {}
        old_json['statistics'] = data
        session = db.session
        self.json = old_json
        session.add(self)
        session.commit()
        return self.json.get("statistics")

    @property
    def name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __str__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.user_id)

    def __repr__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ClientProspect(db.Model):
    __tablename__ = "client_prospect"

    id = db.Column(postgresql.INTEGER, primary_key=True)

    user_id = db.Column(Integer, ForeignKey("users.user_id"),
            index=True)
    user = relationship('User', \
            foreign_keys='ClientProspect.user_id')

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"),
            index=True)
    prospect = relationship("Prospect", \
            foreign_keys="ClientProspect.prospect_id")
    processed = db.Column(Boolean, default=False)
    good = db.Column(Boolean, default=False)
    created = db.Column(Date, default=datetime.datetime.today)

    lead_score = db.Column(Integer, nullable=False)
    stars = db.Column(Integer)
    referrers = db.Column(JSON, default=[])
    extended = db.Column(Boolean)

    #contains sources
    email_addresses = db.Column(JSONB)
    
    def __repr__(self):
        return '{} {}'.format(self.prospect.linkedin_url, self.user.name)

