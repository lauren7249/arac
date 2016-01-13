import os, re, json, numpy, sys, traceback, string, datetime
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, DateTime, Text, BigInteger, Float, TIMESTAMP, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL
from prime import db
import dateutil.parser
from prime.processing_service.helper import uu
from sqlalchemy import and_, not_
from cached_property import cached_property

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        return instance

class Prospect(db.Model):
    __tablename__ = 'prospect'
    __table_args__ = {'extend_existing':True}

    #internal fields
    id = db.Column(Integer, primary_key=True)
    updated = db.Column(DateTime, index=True)

    #linkedin raw fields
    linkedin_name = db.Column(String(1024))
    linkedin_url = db.Column(String(1024), index=True)
    linkedin_id = db.Column(String(1024), index=True)
    linkedin_image_url = db.Column(String(1024))
    linkedin_location_raw = db.Column(String(1024))
    linkedin_headline = db.Column(String(1024))
    linkedin_industry_raw = db.Column(String(1024))
    linkedin_connections = db.Column(Integer)
    linkedin_json = db.Column(JSONB)

    #abstract, right now only from linkedin
    jobs = relationship('Job', foreign_keys='Job.prospect_id')
    schools = relationship('Education', foreign_keys='Education.prospect_id')

    #derived fields, could be useful later
    lat = db.Column(Float)
    lng = db.Column(Float)
    indeed_salary = db.Column(Integer)
    glassdoor_salary = db.Column(Integer)
    dob_min_year = db.Column(Integer)
    dob_max_year = db.Column(Integer)

    email_addresses = db.Column(JSONB)
    profile_image_urls = db.Column(JSONB)

    #clean, normalized, curated profile fields for list UI/filtering
    company = db.Column(String(1024))
    company_website = db.Column(String(1024))
    company_headquarters = db.Column(String(1024))
    job = db.Column(String(1024))
    name = db.Column(String(1024))
    main_profile_image = db.Column(String(1024))
    main_profile_url = db.Column(String(1024))
    mailto = db.Column(String(1024))
    phone = db.Column(String(100))
    #social profiles
    facebook = db.Column(String(1024))
    twitter = db.Column(String(1024))
    angel = db.Column(String(1024))
    flickr = db.Column(String(1024))
    soundcloud = db.Column(String(1024))
    slideshare = db.Column(String(1024))
    plus = db.Column(String(1024))
    pinterest = db.Column(String(1024))
    amazon = db.Column(String(1024))
    linkedin = db.Column(String(1024))
    foursquare = db.Column(String(1024))
    github = db.Column(String(1024))
    #for filtering and network summary: TODO: ADD IN
    industry_category = db.Column(String(100), index=True)
    industry_icon = db.Column(String(200))
    us_state = db.Column(String(200))

    #fields for network summary only
    gender = db.Column(String(15))
    college_grad = db.Column(Boolean)
    wealthscore = db.Column(Integer)
    age = db.Column(Float)

    @property
    def image(self):
        if self.main_profile_image:
            return self.main_profile_image
        return "/static/img/person_image.png"

    @property
    def headline(self):
        if self.linkedin_headline:
            return self.linkedin_headline
        if self.company and self.job:
            return "{} at {}".format(self.job, self.company)
        if self.company:
            return "Works at {}".format(self.company)
        if self.job:
            return self.job
        return ""

    @property
    def tags(self):
        jobs = list(set([c.company_name for c in self.jobs if c.company_name]))[:4]
        schools = list(set([s.school_name for s in self.schools]))[:4]
        return jobs + schools

    @property
    def emails(self):
        return ", ".join([str(e) for e in self.email_addresses])

    def __repr__(self):
        return '<Prospect id={0} url={1}>'.format(self.id, uu(self.main_profile_url))

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
        return out

class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(Integer, primary_key=True)

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Job.prospect_id')
    company_name = db.Column(String(1024))
    #company_url = db.Column(String(1024))
    title = db.Column(String(1024))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    location = db.Column(String(1024))

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                uu(self.company_name),
                uu(self.prospect.linkedin_name)
                )

class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(Integer, primary_key=True)

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Education.prospect_id')
    school_name = db.Column(String(1024))
    #school_url = db.Column(String(1024))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    degree = db.Column(String(1024))

    def __repr__(self):
        return '<Education id={0} name={1} user={2}>'.format(
                self.id,
                uu(self.school_name),
                uu(self.prospect.linkedin_name)
                )


class CloudspongeRecord(db.Model):
    __tablename__ = "cloudsponge_raw"
    id = db.Column(Integer, primary_key=True)
    user_email = db.Column(String(500), index=True) #the email address identityfing the user in linkedin
    account_email = db.Column(String(500), index=True) #one of the email accounts the user authed in with
    contact_email = db.Column(String(500), index=True) #the first email address for the user's contact
    service = db.Column(String(500), index=True)
    contact = db.Column(JSONB)

    #nice to haves
    user_firstname = db.Column(String(500))
    user_lastname = db.Column(String(500))
    user_url = db.Column(String(500))
    user_location = db.Column(String(500))

    @property
    def get_job_title(self):
        return self.contact.get("job_title")

    @property
    def get_company(self):
        if self.contact.get("companies"):
            return self.contact.get("companies")[0]
        return None

    @property
    def get_emails(self):
        all_emails = []
        info = self.contact
        emails = info.get("email",[{}])
        for email in emails:
            address = email.get("address").lower()
            if address: all_emails.append(address)
        return all_emails
