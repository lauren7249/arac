import os
import datetime
import logging
import json
from flask import current_app
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from sqlalchemy import CheckConstraint
import sqlalchemy.event
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date, DateTime, \
        Text, Enum, Float
from sqlalchemy.dialects.postgresql import JSONB
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
    email = db.Column(String(100), nullable=False, unique=True, index=True)
    _password_hash = db.Column('password_hash', String(100), nullable=False)
    is_admin = db.Column(postgresql.BOOLEAN, nullable=False, server_default="FALSE")
    customer_id = db.Column(Integer, ForeignKey("customers.id"))
    customer = relationship('Customer', foreign_keys='User.customer_id')

    linkedin_id = db.Column(String(1024))
    linkedin_url = db.Column(String(1024))
    created = db.Column(DateTime, default=datetime.datetime.today())

    prospects = db.relationship('Prospect', secondary="client_prospect", backref=db.backref('prospects', lazy='dynamic'))
    client_prospects = db.relationship('ClientProspect', backref=db.backref('client_prospects'))
    onboarding_code = db.Column(String(40))
    json = db.Column(JSONB, default={})

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
        return self.client_prospects and len(self.client_prospects) > 0

    def build_statistics(self):
        """
        Calculate most popular schools,
        industries, average gender, age, college degree, and wealth score
        """
        schools = {}
        industries = {}
        gender = {"female":0,"male":0,"unknown":0}
        college_degree = {True:0,False:0,None:0}
        wealth_score = [prospect.wealthscore for prospect in self.prospects if prospect.wealthscore ]
        average_age = [prospect.age for prospect in self.prospects if prospect.age]
        extended_count = 0
        first_degree_count = 0
        for client_prospect in self.client_prospects:
            if client_prospect.extended:
                extended_count+=1
                continue
            first_degree_count+=1
            college_degree[client_prospect.prospect.college_grad] += 1
            gender[client_prospect.prospect.gender] += 1
            industries[client_prospect.prospect.industry_category] = industries.get(client_prospect.prospect.industry_category, 0) + 1
            for school in client_prospect.common_schools:
                schools[school] = schools.get(school, 0) + 1
        males = float(gender["male"])
        females = float(gender["female"])

        #Can't divide by 0
        if females == 0:
            female_percentage = 0
        else:
            female_percentage = females/float(males + females) * 100

        if males == 0:
            male_percentage = 0
        else:
            male_percentage = males/float(males + females) * 100

        data = {"schools": schools,
                "network_size": first_degree_count,
                "count_extended": extended_count,
                "industries": industries,
                "male_percentage": male_percentage,
                "female_percentage": female_percentage,
                "college_percentage": float(college_degree[True])/float(college_degree[True] + college_degree[False]) * 100,
                "average_age": sum(average_age)/len(average_age),
                "wealth_score": sum(wealth_score)/len(wealth_score)}
        return data

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
    created = db.Column(DateTime, default=datetime.datetime.today())
    updated = db.Column(DateTime)

    extended = db.Column(Boolean, default=False)
    referrers = db.Column(JSONB, default=[])
    lead_score = db.Column(Integer)
    stars = db.Column(Integer)
    common_schools = db.Column(JSONB, default=[])

    def __repr__(self):
        return '{} {}'.format(self.prospect.linkedin_url, self.user.name)

    def to_json(self):
        out = {}
        for c in self.__table__.columns:
            key = c.name
            val = getattr(self, c.name)
            if not val:
                continue
            try:
                out[key] = json.dumps(val)
            except Exception, e:
                print str(e)
                pass
        out.update(self.prospect.to_json())
        return out
