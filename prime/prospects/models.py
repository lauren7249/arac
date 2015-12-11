import os, re, json, numpy, sys, traceback, string, datetime
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text, BigInteger, Float, TIMESTAMP, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL
from prime import db
import dateutil.parser
from sqlalchemy import and_, not_

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

class Prospect(db.Model):
    __tablename__ = 'prospect'
    __table_args__ = {'extend_existing':True}

    #internal fields
    id = db.Column(Integer, primary_key=True)
    updated = db.Column(Date, index=True)

    #linkedin raw fields
    linkedin_name = db.Column(String(1024))
    linkedin_url = db.Column(String(1024), index=True)
    linkedin_id = db.Column(String(1024), index=True)
    linkedin_image_url = db.Column(String(1024))
    linkedin_location_raw = db.Column(String(1024))
    linkedin_headline = db.Column(String(1024))
    linkedin_industry_raw = db.Column(String(1024))
    linkedin_connections = db.Column(Integer)

    #abstract, right now only from linkedin
    jobs = relationship('Job', foreign_keys='Job.prospect_id')
    schools = relationship('Education', foreign_keys='Education.prospect_id')

    #derived fields, could be useful later
    lat = db.Column(Float)
    lng = db.Column(Float)
    email_addresses = db.Column(JSONB)
    dob_min = db.Column(Date)
    dob_max = db.Column(Date)
    salary = db.Column(Integer)
    company_linkedin_url = db.Column(CIText())
    company_website = db.Column(CIText())
    company_headquarters = db.Column(String(500))

    #clean, normalized, curated profile fields for list UI/filtering
    company = db.Column(String(1024))
    job = db.Column(String(1024))
    name = db.Column(String(1024))
    image_url = db.Column(String(1024))
    url = db.Column(String(1024))
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
    mailto = db.Column(String(1024)) 
    phone = db.Column(String(100)) 
    common_school = db.Column(String(200))
    industry = db.Column(String(200)) 
    industry_category = db.Column(String(100))
    industry_icon = db.Column(String(200)) 

    #fields for network summary only
    gender = db.Column(String(15))
    college_grad = db.Column(Boolean)
    wealthscore = db.Column(Integer)
    age = db.Column(Float)

    def __repr__(self):
        return '<Prospect id={0} url={1}>'.format(self.id, self.url)

class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(Integer, primary_key=True)

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Job.prospect_id')
    company_name = db.Column(String(1024))
    title = db.Column(String(1024))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    location = db.Column(String(1024))

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                self.company_name,
                self.prospect.linkedin_name
                )

class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(Integer, primary_key=True)

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Education.prospect_id')
    school_name = db.Column(String(1024))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    degree = db.Column(String(1024))

    def __repr__(self):
        return '<Education id={0} name={1} user={2}>'.format(
                self.id,
                self.school_name,
                self.prospect.linkedin_name
                )

