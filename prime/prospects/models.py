import string
import random
import datetime
import json
import requests
import lxml.html
import pandas
import shutil
import os, re, json, numpy, sys
from prime.utils import headers, get_bucket
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text, BigInteger, Float, TIMESTAMP, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSON, TSVECTOR, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL
from prime import db
from citext import CIText
from prime.prospects.get_prospect import session, from_url, from_prospect_id
import dateutil.parser
from boto.s3.key import Key
from requests import HTTPError
import unirest
from random import shuffle
from sqlalchemy import and_, not_
import os
import scipy.stats as stats
import multiprocessing
import traceback

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

class Prospect(db.Model):
    __tablename__ = 'prospect'
    __table_args__ = {'extend_existing':True}
    id = db.Column(Integer, primary_key=True)

    url = db.Column(String(1024), index=True)
    name = db.Column(String(1024))
    linkedin_id = db.Column(String(1024), index=True)

    location_id = db.Column(Integer, ForeignKey("location.id"))
    location = relationship('Location', foreign_keys='Prospect.location_id')
    location_raw = db.Column(String)
    lat = db.Column(Float)
    lng = db.Column(Float)

    image_url = db.Column(String(1024))
    headline = db.Column(String(1024))
    industry = db.Column(Integer, ForeignKey("industry.id"))
    industry_raw = db.Column(String(1024))

    s3_key = db.Column(String(1024), index=True)
    complete = db.Column(Boolean)
    updated = db.Column(Date, index=True)
    connections = db.Column(Integer)
    json = db.Column(JSON)

    google_network_search = db.Column(JSON)
    pipl_response = db.Column(JSON)
    pipl_contact_response = db.Column(JSON)
    jobs = relationship('Job', foreign_keys='Job.prospect_id')
    schools = relationship('Education', foreign_keys='Education.prospect_id')

    all_email_addresses = db.Column(JSON)

    @classmethod
    def linkedin_exists(cls, session, linkedin_id):
        (ret, ) = session.query(exists().where(
            Prospect.linkedin_id==linkedin_id
        ))
        return ret[0]

    @classmethod
    def s3_exists(cls, session, s3_key):
        (ret, ) = session.query(exists().where(
            Prospect.s3_key==s3_key
        ))
        return ret[0]

    @property
    def get_url(self):
        return "/prospect/{}".format(self.id)

    @property
    def get_indeed_salary(self):
        if self.current_job:
            return self.current_job.get_indeed_salary
        job = self.get_job
        if not job:
            return None
        salary = get_indeed_salary(job.get("title"), location=job.get("location"))
        return salary

    @property
    def get_glassdoor_salary(self):
        if self.current_job:
            return self.current_job.get_glassdoor_salary
        job = self.get_job
        if not job:
            return None
        salary = get_glassdoor_salary(job.get("title"))
        return salary

    @property
    def get_max_salary(self):
        if self.current_job:
            return self.current_job.get_max_salary
        return max(self.get_glassdoor_salary, self.get_indeed_salary)

    @property
    def current_job(self):
        jobs = self.jobs
        if len(jobs) > 0:
            present_jobs = [job for job in jobs if job.end_date is None]
            if len(present_jobs):
                start_date_jobs = [job for job in present_jobs if job.start_date]
            else:
                start_date_jobs = [job for job in jobs if job.start_date]
            if len(start_date_jobs) == 0:
                return jobs[0]
            return sorted(start_date_jobs, key=lambda x:x.start_date, reverse=True)[0]
        return None

    @property
    def get_pipl_response(self) :
        content = {}
        if self.pipl_response and self.pipl_response.get("@http_status_code")!=403:
            return self.pipl_response
        content = query_pipl(linkedin_id=self.linkedin_id)
        if content:
            self.pipl_response = content
            session.add(self)
            session.commit()
        return content

    @property
    def get_pipl_contact_response(self) :
        pipl_url ="http://api.pipl.com/search/v3/json/?key=" + pipl_api_key + "&pretty=true"
        content = {}
        if self.pipl_contact_response:
            content = self.pipl_contact_response
        else:
            try:
                url = pipl_url + "&username=" + str(self.linkedin_id) + "@linkedin"
                response = requests.get(url)
                content = json.loads(response.content)
                self.pipl_response = content
                session.add(self)
                session.commit()
            except:
                pass
        return content

    @property
    def age(self):
        dob_year = self.dob_year
        if not dob_year: return None
        return datetime.datetime.today().year - dob_year

    @property
    def dob_year(self):
        dob_year_range = self.dob_year_range
        if not max(dob_year_range): return None
        return numpy.mean(dob_year_range)

    @property
    def has_college_degree(self):
        if not self.schools: return False
        for school in self.schools:
            if school.school_linkedin_id or school.name.lower().find('university')>-1 or school.name.lower().find('college')>-1:
                return True
            if school.degree:
                clean_degree = re.sub('[^0-9a-z\s]','',school.degree.lower())
                if re.search('^bs($|\s)', clean_degree) or re.search('^ba($|\s)', clean_degree) or re.search('^ab($|\s)', clean_degree): return True
        return False

    @property
    def dob_year_range(self):
        first_school_year = None
        first_grad_year = None
        first_weird_school_year = None
        first_weird_grad_year = None
        dob_year_min = None
        dob_year_max = None
        if self.schools:
            for school in self.schools:
                if school.school_linkedin_id or school.name.lower().find('university')>-1 or school.name.lower().find('college')>-1:
                    if school.start_date and (not first_school_year or school.start_date.year<first_school_year): first_school_year = school.start_date.year
                    if school.end_date and (not first_grad_year or school.end_date.year<first_grad_year): first_grad_year = school.end_date.year
                else:
                    if school.start_date and (not first_weird_school_year or school.start_date.year<first_weird_school_year): first_weird_school_year = school.start_date.year
                    if school.end_date and (not first_weird_grad_year or school.end_date.year<first_weird_grad_year): first_weird_grad_year = school.end_date.year

        if first_school_year:
            dob_year_max = first_school_year - 17
            dob_year_min = first_school_year - 20
        elif first_grad_year:
            dob_year_max = first_grad_year - 21
            dob_year_min = first_grad_year - 25
        if dob_year_min: return (dob_year_min, dob_year_max)

        first_year_experience = None
        first_quitting_year = None
        if self.jobs:
            for job in self.jobs:
                if job.start_date and (not first_year_experience or job.start_date.year<first_year_experience): first_year_experience = job.start_date.year
                if job.end_date and (not first_quitting_year or job.end_date.year<first_quitting_year): first_quitting_year = job.end_date.year

        if first_year_experience:
            dob_year_max = first_year_experience - 18
            dob_year_min = first_year_experience - 24
        elif first_quitting_year:
            dob_year_max = first_quitting_year - 19
            dob_year_min = first_quitting_year - 28

        #add age-based fuzz factor for people who only list job years
        if dob_year_min:
            dob_year_min -= (datetime.datetime.today().year - dob_year_min)/10
            return (dob_year_min, dob_year_max)

        if first_weird_school_year:
            dob_year_max = first_weird_school_year - 14
            dob_year_min = first_weird_school_year - 22
        elif first_weird_grad_year:
            dob_year_max = first_weird_grad_year - 17
            dob_year_min = first_weird_grad_year - 27
        return (dob_year_min, dob_year_max)

    @property
    def email(self):
        if self.json:
            return self.json.get("email")
        return None

    @property
    def wealth_percentile(self):
        max_salary = self.get_max_salary
        if max_salary is None: return None
        return get_salary_percentile(max_salary)

    @property
    def wealthscore(self):
        session = db.session
        score = session.query(ProspectWealthscore).filter(ProspectWealthscore.prospect_id == self.id).first()
        if score:
            return score.wealthscore
        return None

    def to_json(self, no_fk=False):
        data = {
            "name": self.name,
            "id": self.id,
            "industry": self.industry_raw,
            "location": self.location_raw,
            "connections": self.connections,
            "url": self.url,
            "image_url": self.image_url,
            "wealthscore": self.wealthscore if self.wealthscore else 56,
            "email": self.email,
            "social_accounts": self.social_accounts}
        if not no_fk:
            data['jobs'] = [job.to_json for job in self.jobs]
            data['current_job'] = "{}, {}".format(uu(self.current_job.title),\
                                        uu(self.current_job.company.name)) if self.current_job \
                                        else "N/A"
            data['schools'] = [school.to_json for school in self.schools]
            #data["news"] =  self.relevant_content
        return data

    def __repr__(self):
        return '<Prospect id={0} url={1}>'.format(self.id, self.url)


class ProspectGender(db.Model):
    __tablename__ = "prospect_gender"

    prospect_id = db.Column(BigInteger, primary_key=True)
    gender = db.Column(Boolean)

    def __repr__(self):
        return '<Prospect Gender prospect_id={0}>'.format(
                self.prospect_id
                )

class ProspectWealthscore(db.Model):
    __tablename__ = "prospect_wealthscore"

    prospect_id = db.Column(BigInteger, primary_key=True)
    wealthscore = db.Column(Integer)

    def __repr__(self):
        return '<Prospect Wealthscore prospect_id={0} wealthscore={1}>'.format(
                self.prospect_id,
                self.wealthscore
                )

class Industry(db.Model):
    __tablename__ = "industry"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<Industry id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<Company id={0} name={1}>'.format(
                self.id,
                self.name
                )

class LinkedinSchool(db.Model):
    __tablename__ = "linkedin_schools"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(900))
    pretty_url = db.Column(String(150))
    image_url = db.Column(String(900))

    def __repr__(self):
        return '<School id={0} name={1}>'.format(
                self.id,
                self.name
                )

class LinkedinCompany(db.Model):
    __tablename__ = "linkedin_companies"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(900))
    industry = db.Column(String(200))
    company_type = db.Column(String(200))
    description = db.Column(Text)
    pretty_url = db.Column(String(150))
    image_url = db.Column(String(900))
    founded = db.Column(Integer)
    headquarters = db.Column(String(500))
    min_employees = db.Column(Integer)
    max_employees = db.Column(Integer)
    specialties = db.Column(ARRAY(String(200)))
    website = db.Column(CIText())
    clearbit_response = db.Column(JSON)

    @property
    def get_clearbit_response(self):
        if self.clearbit_response and not self.clearbit_response.get("pending"): return self.clearbit_response
        if not self.website: return None
        website = self.website.replace("http://","").replace("https://","")
        if not website: return None
        company = clearbit.Company.find(domain=website)
        self.clearbit_response = company
        session.add(self)
        session.commit()
        return self.clearbit_response

    def __repr__(self):
        return '<Company id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(Integer, primary_key=True)
    company_id = db.Column(Integer, ForeignKey("company.id"), index=True)
    company = relationship('Company', foreign_keys='Job.company_id')
    location = db.Column(String(1024))

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Job.prospect_id')
    title = db.Column(String(1024))
    fts_title = db.Column(TSVECTOR)
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    company_linkedin_id = db.Column(Integer, ForeignKey("linkedin_companies.id"), index=True)
    linkedin_company = relationship('LinkedinCompany', foreign_keys='Job.company_linkedin_id')
    indeed_salary = db.Column(Integer)
    glassdoor_salary = db.Column(Integer)

    @property
    def name(self):
        return self.company.name

    @property
    def to_json(self):
        date_to_str = lambda x:x.strftime("%Y") if x else ""
        if not self.end_date:
            dates = "{} - Present".format(date_to_str(self.start_date))
        else:
            dates = "{} - {}".format(
                    date_to_str(self.start_date),
                    date_to_str(self.end_date))
        return {"company_name":self.company.name,
                "title": self.title,
                "location": self.location,
                "dates": dates}

    @property
    def get_max_salary(self):
        return max(self.get_glassdoor_salary, self.get_indeed_salary)

    @property
    def get_indeed_salary(self):
        if self.indeed_salary:
            return self.indeed_salary
        jobtitle = get_or_create(session, JobTitle, title=self.title)
        salary = jobtitle.get_indeed_salary
        if salary:
            self.indeed_salary = salary
            session.add(self)
            session.commit()
        return self.indeed_salary

    @property
    def get_glassdoor_salary(self):
        if self.glassdoor_salary:
            return self.glassdoor_salary
        jobtitle = get_or_create(session, JobTitle, title=self.title)
        salary = jobtitle.get_glassdoor_salary
        if salary:
            self.glassdoor_salary = salary
            session.add(self)
            session.commit()
        return self.glassdoor_salary

    @property
    def get_url(self):
        return "/company/{}".format(self.company.id)

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                self.company.name,
                self.prospect.name
                )


class JobTitle(db.Model):
    __tablename__ = "job_titles"
    title = db.Column(String(1024), primary_key=True)
    indeed_salary = db.Column(Integer)
    glassdoor_salary = db.Column(Integer)

    @property
    def get_max_salary(self):
        return max(self.get_glassdoor_salary, self.get_indeed_salary)

    @property
    def get_indeed_salary(self):
        if self.indeed_salary:
            return self.indeed_salary
        salary = get_indeed_salary(self.title)
        if salary:
            self.indeed_salary = salary
            session.add(self)
            session.commit()
        return self.indeed_salary

    @property
    def get_glassdoor_salary(self):
        if self.glassdoor_salary:
            return self.glassdoor_salary
        salary = get_glassdoor_salary(self.title)
        if salary:
            self.glassdoor_salary = salary
            session.add(self)
            session.commit()
        return self.glassdoor_salary


class ProspectUrl(db.Model):
    __tablename__ = "prospect_urls"

    url = db.Column(CIText(), primary_key=True)
    linkedin_id = db.Column(BigInteger)

    def __repr__(self):
        return '<url ={0} linkedin_id={1}>'.format(
                self.url,
                self.linkedin_id
                )


class School(db.Model):
    __tablename__ = "school"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<School id={0} name={1}>'.format(
                self.id,
                self.name
                )


class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(Integer, primary_key=True)
    school_id = db.Column(Integer, ForeignKey("school.id"), index=True)
    school = relationship('School', foreign_keys='Education.school_id')
    degree = db.Column(String(200))
    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Education.prospect_id')
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    school_linkedin_id = db.Column(Integer, ForeignKey("linkedin_schools.id"), index=True)
    linkedin_school = relationship('LinkedinSchool', foreign_keys='Education.school_linkedin_id')

    @property
    def name(self):
        return self.school.name

    @property
    def to_json(self):
        date_to_str = lambda x:x.strftime("%Y") if x else ""
        return {"school_name":self.school.name,
                "degree": self.degree,
                "graduation": date_to_str(self.end_date)}

    @property
    def get_url(self):
        return "/school/{}".format(self.school.id)

    def __repr__(self):
        return '<Education id={0} name={1} user={2}>'.format(
                self.id,
                self.school.name,
                self.prospect.name
                )


class Location(db.Model):
    __tablename__ = "location"

    id = db.Column(BigInteger, primary_key=True)
    name = db.Column(CIText())
    lat = db.Column(Float)
    lng = db.Column(Float)

    def __repr__(self):
        return '<Location id={0} name={1}>'.format(
                self.id,
                self.name
                )


class ProspectLocation(db.Model):
    __tablename__ = "prospect_location"

    prospect_id = db.Column(BigInteger, primary_key=True)
    location_id = db.Column(BigInteger, primary_key=True)

    def __repr__(self):
        return '<Prospect Location prospect_id={0} location_id={1}>'.format(
                self.prospect_id,
                self.location_id
                )

