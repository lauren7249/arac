import os
import hashlib
import sys
import json
import traceback
from collections import Counter
import datetime
import logging
from flask import current_app, render_template
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
from prime.processing_service.helper import uu
from prime.utils import random_string
from prime.utils.email import sendgrid_email
from prime.customers.models import Customer
from prime import login_manager, db
from flask.ext.sqlalchemy import SQLAlchemy

reload(sys)
sys.setdefaultencoding('utf-8')

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
    manager_id = db.Column(Integer, index=True)

    linkedin_id = db.Column(String(1024))
    linkedin_url = db.Column(String(1024))
    linkedin_location = db.Column(String(1024))
    linkedin_industry = db.Column(String(1024))
    image_url = db.Column(String(1024))
    linkedin_email = db.Column(String(1024))
    created = db.Column(DateTime, default=datetime.datetime.today())

    unique_contacts_uploaded = db.Column(Integer, default=0)
    contacts_from_linkedin = db.Column(Integer, default=0)
    contacts_from_gmail = db.Column(Integer, default=0)
    contacts_from_yahoo = db.Column(Integer, default=0)
    contacts_from_windowslive = db.Column(Integer, default=0)
    account_sources = db.Column(JSONB, default={})

    prospects = db.relationship('Prospect', secondary="client_prospect",
            backref=db.backref('prospects'), lazy="dynamic")
    client_prospects = db.relationship('ClientProspect', backref=db.backref('client_prospects'))
    onboarding_code = db.Column(String(40))

    account_created = db.Column(postgresql.BOOLEAN, default=False)
    hiring_screen_completed = db.Column(postgresql.BOOLEAN, default=False)
    p200_started = db.Column(postgresql.BOOLEAN, default=False)
    p200_completed = db.Column(postgresql.BOOLEAN, default=False)
    p200_submitted_to_manager = db.Column(postgresql.BOOLEAN, default=False)
    p200_approved = db.Column(postgresql.BOOLEAN, default=False)
    _statistics = db.Column(JSONB, default={})

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"))
    prospect = relationship("Prospect", \
            foreign_keys="User.prospect_id", lazy='joined')

    def __init__(self, first_name, last_name, email, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.first_name = first_name.title()
        self.last_name = last_name.title()
        self.email = email.lower()
        self.set_password(password)

    @property 
    def hired(self):
        return self.p200_started or self.p200_completed or self.p200_submitted_to_manager or self.p200_approved        
        
    @property
    def status(self):
        if self.p200_completed:
            return "p200_completed"
        if self.p200_started:
            return "p200_started"
        if self.hiring_screen_completed:
            return "hiring_screen_completed"
        return "new_hire"

    @property
    def image(self):
        if self.image_url:
            return self.image_url
        return "/static/img/shadow-avatar.png"

    @property
    def p200_count(self):
        return max(200 - int(self.prospects.filter(ClientProspect.good==True).count()), 0)

    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    def is_active(self):
        return True

    @property
    def is_manager(self):
        return (len(self.manager_profile)>0)

    def get_id(self):
        return unicode(self.user_id)

    @property
    def generate_reset_token(self):
        code = random_string(10).encode('utf-8')
        password = hashlib.md5(code).hexdigest()
        self.onboarding_code = password
        db.session.add(self)
        db.session.commit()
        return code

    def send_reset_password(self):
        code = self.generate_reset_token
        body = render_template("emails/reset.html",
                base_url=current_app.config.get("BASE_URL"), code=code)
        subject = "Advisorconnect Password Reset"
        sendgrid_email(self.email, subject, body)
        return True

    def invite(self):
        code = self.generate_reset_token
        body = render_template("emails/invite.html", manager=self.manager, agent=self,
                base_url=current_app.config.get("BASE_URL"), code=code)
        subject = "Invitation from New York Life"
        sendgrid_email(self.email, subject, body, from_email=self.manager.user.email)
        return True

    def submit_to_manager(self):
        body = render_template("emails/p200_submitted.html", agent=self,
                base_url=current_app.config.get("BASE_URL"))
        subject = "{} submitted a P200 for approval".format(self.name)
        sendgrid_email(self.manager.user.email, subject, body,
                from_email="jeff@advisorconnect.co")
        return True

    def p200_manager_approved(self):
        body = render_template("emails/p200_manager_approved.html", manager=self.manager, agent=self,
                base_url=current_app.config.get("BASE_URL"))
        subject = "Your P200 is Ready to Export"
        sendgrid_email(self.email, subject, body,
                from_email="jeff@advisorconnect.co")
        return True

    @property
    def manager(self):
        from prime.managers.models import ManagerProfile
        if self.manager_id:
            return db.session.query(ManagerProfile).get(self.manager_id)
        return None

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
        db.session.commit()
        return u

    @property
    def has_prospects(self):
        return self.client_prospects and len(self.client_prospects) > 0

    def statistics(self, refresh=False):
        if not refresh and self._statistics and self._statistics.get("network_size"):
            return self._statistics
        stats = self.build_statistics()
        self._statistics = stats
        db.session.add(self)
        db.session.commit()
        return stats

    @property
    def from_linkedin(self):
        return self.statistics().get("from_linkedin", 0)

    @property
    def from_gmail(self):
        return self.statistics().get("from_gmail", 0)

    @property
    def from_yahoo(self):
        return self.statistics().get("from_yahoo", 0)

    @property
    def from_windowslive(self):
        return self.statistics().get("from_windowslive", 0)


    @property
    def linkedin(self):
        return self.statistics().get("linkedin", 0)

    @property
    def facebook(self):
        return self.statistics().get("facebook", 0)

    @property
    def twitter(self):
        return self.statistics().get("twitter", 0)

    @property
    def pinterest(self):
        return self.statistics().get("pinterest", 0)

    @property
    def amazon(self):
        return self.statistics().get("amazon", 0)

    @property
    def primary_network_size(self):
        return self.statistics().get("network_size", 0)

    @property
    def extended_network_size(self):
        return self.statistics().get("count_extended", 0)

    @property
    def total_network_size(self):
        return self.primary_network_size + self.extended_network_size

    @property
    def industries(self):
        results = []
        for industry_category, count in self.statistics().get("industries").iteritems():
            from prime.processing_service.constants import CATEGORY_ICONS
            industry_icon = CATEGORY_ICONS.get(industry_category)
            if industry_category and industry_icon:
                results.append((industry_category, count,industry_icon, ))
        return sorted(results, key = lambda tup:tup[1], reverse=True)[:10]

    @property
    def states(self):
        states = []
        for state, count in self.statistics().get("locations").iteritems():
            states.append((state, count,))
        return states

    @property
    def average_age(self):
        try:
            return int(self.statistics().get("average_age"))
        except:
            return None

    @property
    def female_percentage(self):
        try:
            return int(self.statistics().get("female_percentage"))
        except:
            return "N/A"

    @property
    def male_percentage(self):
        try:
            return int(self.statistics().get("male_percentage"))
        except:
            return "N/A"

    @property
    def college_percentage(self):
        try:
            return int(self.statistics().get("college_percentage"))
        except:
            return "N/A"

    @property
    def average_income_score(self):
        return self.statistics().get("wealth_score")

    def build_statistics(self):
        """
        Calculate most popular schools,
        industries, average gender, age, college degree, and wealth score
        """
        schools = {}
        industries = {}
        locations = {}
        gender = {"female":0,"male":0,"unknown":0}
        college_degree = {True:0,False:0,None:0}
        wealth_score = []
        average_age = []
        extended_count = 0
        first_degree_count = 0
        facebook = 0
        linkedin = 0
        twitter = 0
        amazon = 0
        pinterest = 0
        from_linkedin = 0
        from_gmail = 0
        from_yahoo = 0
        from_windowslive = 0
        account_sources = self.account_sources
        for client_prospect in self.client_prospects:
            if not client_prospect.stars:
                logger.warn("{} has stars=None (ClientProspect id={})".format(uu(client_prospect.prospect.name), client_prospect.id))
                continue
            if client_prospect.extended:
                extended_count+=1
                continue
            for source in client_prospect.sources:
                source = account_sources.get(source)
                if source=='linkedin':
                    from_linkedin+=1
                elif source=='gmail':
                    from_gmail+=1
                elif source=='yahoo':
                    from_yahoo+=1
                elif source =='windowslive':
                    from_windowslive+=1
            if not client_prospect.prospect:
                logger.warn("clientprospect=None (clientprospect id={})".format(client_prospect.id))
                continue
            if client_prospect.prospect.wealthscore:
                wealth_score.append(client_prospect.prospect.wealthscore)
            if client_prospect.prospect.age:
                average_age.append(client_prospect.prospect.age)
            if client_prospect.prospect.facebook: facebook+=1
            if client_prospect.prospect.linkedin_url or client_prospect.prospect.linkedin: linkedin+=1
            if client_prospect.prospect.amazon: amazon+=1
            if client_prospect.prospect.twitter: twitter+=1
            if client_prospect.prospect.pinterest: pinterest+=1
            first_degree_count+=1
            college_degree[client_prospect.prospect.college_grad] += 1
            if client_prospect.prospect.gender:
                gender[client_prospect.prospect.gender] += 1
            else:
                logger.warn("{} has gender=None (prospect id={})".format(uu(client_prospect.prospect.name), client_prospect.prospect_id))
            if client_prospect.prospect.industry_category:
                industries[client_prospect.prospect.industry_category] = industries.get(client_prospect.prospect.industry_category, 0) + 1
            else:
                logger.warn("{} has industry_category=None )".format(client_prospect.prospect.linkedin_industry_raw))
            if client_prospect.prospect and client_prospect.prospect.us_state:
                locations[client_prospect.prospect.us_state] = locations.get(client_prospect.prospect.us_state, 0) + 1
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

        if college_degree[True] + college_degree[False] == 0:
            college_percentage = 0
        else:
            college_percentage = float(college_degree[True])/float(college_degree[True] + college_degree[False]) * 100

        if len(average_age) == 0:
            average_age = 0
        else:
            average_age = sum(average_age)/len(average_age)

        if len(wealth_score) == 0:
            wealth_score = 0
        else:
            wealth_score = sum(wealth_score)/len(wealth_score)

        data = {"schools": schools,
                "network_size": first_degree_count,
                "count_extended": extended_count,
                "industries": industries,
                "male_percentage": male_percentage,
                "female_percentage": female_percentage,
                "locations": locations,
                "college_percentage": college_percentage,
                "average_age": average_age,
                "wealth_score": wealth_score,
                "linkedin": linkedin,
                "facebook": facebook,
                "twitter": twitter,
                "pinterest": pinterest,
                "amazon": amazon,
                "from_linkedin": from_linkedin,
                "from_gmail": from_gmail,
                "from_yahoo": from_yahoo,
                "from_windowslive": from_windowslive}
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
            index=True, nullable=False)
    user = relationship('User', \
            foreign_keys='ClientProspect.user_id')

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"),
            index=True, nullable=False)
    prospect = relationship("Prospect", \
            foreign_keys="ClientProspect.prospect_id", lazy='joined')
    #processed means skipped, needs name change
    processed = db.Column(Boolean, default=False)
    good = db.Column(Boolean, default=False)
    created = db.Column(DateTime, default=datetime.datetime.today())
    updated = db.Column(DateTime)

    extended = db.Column(Boolean, default=False)
    referrers = db.Column(JSONB, default=[])
    lead_score = db.Column(Integer)
    stars = db.Column(Integer)
    common_schools = db.Column(JSONB, default=[])
    sources = db.Column(JSONB, default=[])

    @property
    def stars_display(self):
        try:
            star_dict = {
                    1: 'one-star',
                    2: 'two-star',
                    3: 'three-star',
                    4: 'four-star',
                    5: 'five-star'
                    }
            return star_dict[self.stars]
        except:
            return "three-star"

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
        if self.prospect:
            out.update(self.prospect.to_json())
        return out
