import os
import hashlib
import sys
import json
import traceback
from collections import Counter
import datetime
import logging
from helpers.data_helpers import json_array_to_matrix
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
from prime.processing_service.saved_request import UserRequest
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL
from prime.processing_service.helper import uu, xor_crypt_string, xor_decrypt_string
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

    linkedin_login_email = db.Column(String(500))
    _linkedin_password_hash = db.Column('linkedin_password_hash', String(500))
    linkedin_cookies = db.Column(JSONB, default={})

    unique_contacts_uploaded = db.Column(Integer, default=0)
    contacts_from_linkedin = db.Column(Integer, default=0)
    contacts_from_gmail = db.Column(Integer, default=0)
    contacts_from_yahoo = db.Column(Integer, default=0)
    contacts_from_icloud = db.Column(Integer, default=0)
    contacts_from_aol = db.Column(Integer, default=0)
    contacts_from_windowslive = db.Column(Integer, default=0)
    contacts_from_csv = db.Column(Integer, default=0)
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
    hired = db.Column(postgresql.BOOLEAN, default=False)
    not_hired = db.Column(postgresql.BOOLEAN, default=False)
    not_hired_reason = db.Column(String(500))
    _statistics = db.Column(JSONB, default={})
    _statistics_p200 = db.Column(JSONB, default={})
    all_states = db.Column(JSONB, default={})
    intro_js_seen = db.Column(postgresql.BOOLEAN, default=False)


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
    def location(self):
        if self.is_manager:
            return self.manager_profile[0].address_2
        return self.manager.address_2

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
        return int(self.prospects.filter(ClientProspect.good==True).count())

    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    def set_linkedin_password(self, linkedin_password, session=db.session):
        self._linkedin_password_hash = xor_crypt_string(linkedin_password, self._password_hash[:15])
        session.add(self)
        session.commit()

    @property
    def linkedin_password(self):
        if self._linkedin_password_hash is None:
            return None
        return xor_decrypt_string(self._linkedin_password_hash, self._password_hash[:15])

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
                base_url=current_app.config.get("BASE_URL"),
                logo=current_app.config.get("EMAIL_LOGO"),
                code=code)
        subject = "Advisorconnect Password Reset"
        sendgrid_email(self.email, subject, body)
        return True

    def invite(self):
        code = self.generate_reset_token
        body = render_template("emails/invite.html", agent=self,
                base_url=current_app.config.get("BASE_URL"),
                code=code,
                inviter=current_app.config.get("OWNER"),
                logo=current_app.config.get("EMAIL_LOGO")
                )
        subject = "Invitation from {}".format(current_app.config.get("OWNER"))
        sendgrid_email(self.email, subject, body, from_email=self.manager.user.email)
        return True

    def submit_to_manager(self):
        body = render_template("emails/p200_submitted.html",
                agent=self,
                base_url=current_app.config.get("BASE_URL"),
                logo=current_app.config.get("EMAIL_LOGO")
                )
        subject = "{} submitted a P200 for approval".format(self.name)
        sendgrid_email(self.manager.user.email, subject, body,
                from_email="jeff@advisorconnect.co")
        return True

    def p200_manager_approved(self):
        body = render_template("emails/p200_manager_approved.html",
                agent=self,
                logo=current_app.config.get("EMAIL_LOGO"),
                base_url=current_app.config.get("BASE_URL"))
        subject = "Your P200 is Ready to Export"
        sendgrid_email(self.email, subject, body,
                from_email="jeff@advisorconnect.co")
        return True

    def clear_data(self, remove_uploads=False, session=db.session):
        if remove_uploads:
            user_request = UserRequest(self.email)
            user_request.boto_key.delete()
            self.contacts_from_linkedin = 0
            self.contacts_from_gmail = 0
            self.contacts_from_yahoo = 0
            self.contacts_from_icloud = 0
            self.contacts_from_windowslive = 0
            self.contacts_from_csv = 0
            self.contacts_from_aol = 0
            self.unique_contacts_uploaded = 0
            session.add(self)
            session.commit()
        user_request = UserRequest(self.email, type='actual-p200-data')
        user_request.boto_key.delete()
        user_request = UserRequest(self.email, type='hiring-screen-data')
        user_request.boto_key.delete()

    def refresh_p200_data(self, new_data=[]):
        user_request = UserRequest(self.email, type='actual-p200-data')
        data = user_request.lookup_data()
        #it's been run once and we arent adding anything.
        by_linkedin_id = {}
        for person in data + new_data:
            linkedin_id = person.get("linkedin_data",{}).get("linkedin_id")
            info = by_linkedin_id.get(linkedin_id,{})
            info.update(person)
            sources = info.get("sources",[]) + person.get("sources",[])
            social_accounts = info.get("social_accounts",[])  + person.get("social_accounts",[])
            images = info.get("images",[])  + person.get("images",[])
            email_addresses = info.get("email_addresses",[])  + person.get("email_addresses",[])
            info["sources"] = list(set(sources))
            info["social_accounts"] = list(set(social_accounts))
            info["images"] = list(set(images))
            info["email_addresses"] = list(set(email_addresses))
            by_linkedin_id[linkedin_id] = info
        if new_data:
            user_request._make_request(new_data)
        return by_linkedin_id.values()

    def refresh_hiring_screen_data(self, new_data=[]):
        user_request = UserRequest(self.email, type='hiring-screen-data')
        data = user_request.lookup_data()
        #it's been run once and we arent adding anything.
        by_linkedin_id = {}
        for person in data + new_data:
            linkedin_id = person.get("linkedin_data",{}).get("linkedin_id")
            info = by_linkedin_id.get(linkedin_id,{})
            info.update(person)
            sources = info.get("sources",[]) + person.get("sources",[])
            social_accounts = info.get("social_accounts",[])  + person.get("social_accounts",[])
            images = info.get("images",[])  + person.get("images",[])
            email_addresses = info.get("email_addresses",[])  + person.get("email_addresses",[])
            info["sources"] = list(set(sources))
            info["social_accounts"] = list(set(social_accounts))
            info["images"] = list(set(images))
            info["email_addresses"] = list(set(email_addresses))
            by_linkedin_id[linkedin_id] = info
        if new_data:
            user_request._make_request(by_linkedin_id.values())
        return by_linkedin_id.values()

    def refresh_contacts(self, new_contacts=[], service_filter=None, session=db.session):
        user_request = UserRequest(self.email)
        contacts_array = user_request.lookup_data()
        from_linkedin = set()
        from_gmail = set()
        from_yahoo = set()
        from_icloud = set()
        from_windowslive = set()
        from_csv = set()
        from_aol = set()
        from_all = set()
        account_sources = {}
        by_source = {}
        if not contacts_array:
            contacts_array = []
        for record in contacts_array + new_contacts:
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
                #print contact
            if email_address:
                key = email_address
            elif service=="linkedin":
                key = str(contact.values())
            else:
                key = None
            if not key:
                continue
            by_source[key+service] = record
            from_all.add(key)
            if service_filter and service.lower() != service_filter.lower():
                continue
            if service=='linkedin':
                from_linkedin.add(key)
            elif service=='gmail':
                from_gmail.add(key)
            elif service=='yahoo':
                from_yahoo.add(key)
            elif service=='icloud':
                from_icloud.add(key)                
            elif service=='windowslive':
                from_windowslive.add(key)
            elif service=='csv':
                from_csv.add(key)
            elif service=='aol':
                from_aol.add(key)
            else:
                continue

        self.unique_contacts_uploaded = len(from_all)
        if len(from_linkedin):
            self.contacts_from_linkedin = len(from_linkedin)
        if len(from_gmail):
            self.contacts_from_gmail = len(from_gmail)
        if len(from_yahoo):
            self.contacts_from_yahoo = len(from_yahoo)
        if len(from_icloud):
            self.contacts_from_icloud = len(from_icloud)            
        if len(from_windowslive):
            self.contacts_from_windowslive = len(from_windowslive)
        if len(from_csv):
            self.contacts_from_csv = len(from_csv)
        if len(from_aol):
            self.contacts_from_aol = len(from_aol)
        self.account_sources = account_sources
        self._statistics = None
        self._statistics_p200 = None
        session.add(self)
        session.commit()
        if new_contacts:
            user_request._make_request(by_source.values())
        return by_source.values(), self

    def generate_exclusions_report(self, excluded):
        matrix = json_array_to_matrix(excluded)
        user_request = UserRequest(self.email, type='excluded')
        user_request._make_request(matrix)

    @property
    def exclusions_report(self):
        user_request = UserRequest(self.email, type='excluded')
        matrix = user_request.lookup_data()
        return matrix

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

    def statistics(self, refresh=False, p200=False):
        if not refresh:
            if not p200 and self._statistics and self._statistics.get("network_size"):
                return self._statistics
            if p200 and self._statistics_p200 and self._statistics_p200.get("network_size"):
                return self._statistics_p200
        stats = self.build_statistics(p200=p200)
        if not p200:
            self._statistics = stats
        else:
            self._statistics_p200 = stats
        db.session.add(self)
        db.session.commit()
        return stats

    def from_linkedin(self, p200=False):
        return self.statistics(p200=p200).get("from_linkedin", 0)

    def from_gmail(self, p200=False):
        return self.statistics(p200=p200).get("from_gmail", 0)

    def from_yahoo(self, p200=False):
        return self.statistics(p200=p200).get("from_yahoo", 0)

    def from_icloud(self, p200=False):
        return self.statistics(p200=p200).get("from_icloud", 0)

    def from_windowslive(self, p200=False):
        return self.statistics(p200=p200).get("from_windowslive", 0)

    def from_csv(self, p200=False):
        return self.statistics(p200=p200).get("from_csv", 0)

    def from_aol(self, p200=False):
        return self.statistics(p200=p200).get("from_aol", 0)

    def linkedin(self, p200=False):
        return self.statistics(p200=p200).get("linkedin", 0)

    def facebook(self, p200=False):
        return self.statistics(p200=p200).get("facebook", 0)

    def twitter(self, p200=False):
        return self.statistics(p200=p200).get("twitter", 0)

    def pinterest(self, p200=False):
        return self.statistics(p200=p200).get("pinterest", 0)

    def amazon(self, p200=False):
        return self.statistics(p200=p200).get("amazon", 0)

    def primary_network_size(self, p200=False):
        return self.statistics(p200=p200).get("network_size", 0)

    def extended_network_size(self, p200=False):
        return self.statistics(p200=p200).get("count_extended", 0)

    def total_network_size(self, p200=False):
        return self.primary_network_size(p200=p200) + self.extended_network_size(p200=p200)

    def industries(self, p200=False):
        results = []
        for industry_category, count in self.statistics(p200=p200).get("industries").iteritems():
            from prime.processing_service.constants import CATEGORY_ICONS
            industry_icon = CATEGORY_ICONS.get(industry_category)
            if industry_category and industry_icon:
                results.append((industry_category, count,industry_icon, ))
        return sorted(results, key = lambda tup:tup[1], reverse=True)[:10]

    def states(self, p200=False, all_states=False):
        if all_states and self.all_states:
            locations = self.all_states
        else:
            locations = self.statistics(p200=p200).get("locations")
        states = []
        for state, count in locations.iteritems():
            states.append((state, count,))
        return states

    def average_age(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("average_age")))
        except:
            return None

    def young_professional_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("young_professional_percentage")))
        except:
            return "N/A"

    def pre_retiree_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("pre_retiree_percentage")))
        except:
            return "N/A"

    def retiree_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("retiree_percentage")))
        except:
            return "N/A"

    def female_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("female_percentage")))
        except:
            return "N/A"

    def male_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("male_percentage")))
        except:
            return "N/A"

    def college_percentage(self, p200=False):
        try:
            return int(round(self.statistics(p200=p200).get("college_percentage")))
        except:
            return "N/A"

    def average_income_score(self, p200=False):
        return self.statistics(p200=p200).get("wealth_score")

    #creates edges by linkedin id -- for QA purposes
    @property
    def extended_graph(self):
        g = []
        for client_prospect in self.client_prospects:
            if not client_prospect.referrers:
                continue
            li_1 = client_prospect.prospect.linkedin_id
            name_1 = client_prospect.prospect.name
            for referrer in client_prospect.referrers:
                g.append((referrer.get("referrer_url"), name_1))
        return g

    def build_statistics(self, p200=False):
        """
        Calculate most popular states,
        industries, average gender, age, college degree, and wealth score
        """
        industries = {}
        locations = {}
        gender = {"female":0,"male":0,"unknown":0}
        age_category = {"young_professionals":0, "pre_retirees":0, "retirees":0}
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
        from_icloud = 0
        from_windowslive = 0
        from_csv = 0
        from_aol = 0
        account_sources = self.account_sources
        for client_prospect in self.client_prospects:
            if p200 and not client_prospect.good:
                continue
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
                elif source=='icloud':
                    from_icloud+=1                    
                elif source =='windowslive':
                    from_windowslive+=1
                elif source =='csv':
                    from_csv+=1
                elif source=='aol':
                    from_aol+=1
            if not client_prospect.prospect:
                logger.warn("clientprospect=None (clientprospect id={})".format(client_prospect.id))
                continue
            if client_prospect.prospect.wealthscore:
                wealth_score.append(client_prospect.prospect.wealthscore)
            if client_prospect.prospect.age:
                _age = client_prospect.prospect.age
                average_age.append(_age)
                if _age<45:
                    age_category["young_professionals"]+=1
                elif _age<60:
                    age_category["pre_retirees"]+=1
                else:
                    age_category["retirees"]+=1
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

        young_professionals = float(age_category["young_professionals"])
        pre_retirees = float(age_category["pre_retirees"])
        retirees = float(age_category["retirees"])
        if young_professionals == 0:
            young_professional_percentage = 0
        else:
            young_professional_percentage = young_professionals/float(young_professionals + pre_retirees + retirees) * 100
        if pre_retirees == 0:
            pre_retiree_percentage = 0
        else:
            pre_retiree_percentage = pre_retirees/float(young_professionals + pre_retirees + retirees) * 100
        if retirees == 0:
            retiree_percentage = 0
        else:
            retiree_percentage = retirees/float(young_professionals + pre_retirees + retirees) * 100

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

        data = {"network_size": first_degree_count,
                "count_extended": extended_count,
                "industries": industries,
                "young_professional_percentage": young_professional_percentage,
                "pre_retiree_percentage": pre_retiree_percentage,
                "retiree_percentage": retiree_percentage,
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
                "from_icloud": from_icloud,
                "from_windowslive": from_windowslive,
                "from_csv": from_csv,
                "from_aol": from_aol}
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
    sources = db.Column(JSONB, default=[])

    @property
    def stars_display(self):
        try:
            star_dict = {
                    1: 'one-star',
                    2: 'two-stars',
                    3: 'three-stars',
                    4: 'four-stars',
                    5: 'five-stars'
                    }
            return star_dict[self.stars]
        except:
            return "three-stars"

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
