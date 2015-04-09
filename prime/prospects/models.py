import string
import json
import requests
import lxml.html
import os

from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text, BigInteger, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL

from prime import db
from prime.prospects.helper import BingSearch

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

class Prospect(db.Model):
    __tablename__ = 'prospect'

    id = db.Column(Integer, primary_key=True)

    url = db.Column(String(1024))
    name = db.Column(String(1024))
    linkedin_id = db.Column(String(1024), index=True)

    location = db.Column(Integer)
    location_raw = db.Column(String)

    image_url = db.Column(String(1024))

    industry = db.Column(Integer, ForeignKey("industry.id"))
    industry_raw = db.Column(String(1024))

    s3_key = db.Column(String(1024), index=True)
    complete = db.Column(Boolean)
    updated = db.Column(Date)
    connections = db.Column(Integer)
    json = db.Column(JSON)


    jobs = relationship('Job', foreign_keys='Job.prospect_id')
    schools = relationship('Education', foreign_keys='Education.prospect_id')

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
    def current_job(self):
        jobs = self.jobs
        if len(jobs) > 0:
            start_date_jobs = [job for job in jobs if job.start_date]
            if len(start_date_jobs) == 0:
                return jobs[0]
            return sorted(start_date_jobs, key=lambda x:x.start_date, reverse=True)[0]
        return None

    @property
    def pipl_info(self):
        info = {}
        try:
            base_url ="http://api.pipl.com/search/v3/json/?username="
            linkedin_id = str(self.linkedin_id)
            end_query = "@linkedin&key=uegvyy86ycyvyxjhhbwsuhj9&pretty=true"
            url = "".join([base_url, linkedin_id, end_query])
            response = requests.get(url)
            content = json.loads(response.content)
            emails = content.get('person').get("emails")
            images = content.get('person').get("images")
            if len(emails) > 0:
                info['email'] = emails[0].get("address")
        except:
            pass
        return info


    @property
    def calculate_salary(self):
        if self.current_job:
            position = self.current_job.title
            headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'
                    }
            url =  "http://www.indeed.com/salary?q1=%s&l1=#%s" % (position,
                    self.location_raw)
            try:
                response = requests.get(url, headers=headers)
                clean = lxml.html.fromstring(response.content)
                salary = clean.xpath("//span[@class='salary']")[0].text
                return salary
            except Exception, err:
                pass
        return None

    @property
    def relevant_content(self):
        try:
            company = self.current_job.company.name
            bing = BingSearch("%s %s" % (self.name, company))
            results = bing.search()
            return results[:5]
        except:
            return []

    @property
    def boosted_profiles(self):
        session = db.session
        if self.json:
            boosted_ids = self.json.get("boosted_ids")
            if boosted_ids:
                profiles = []
                extra_prospects = session.query(Prospect).filter(\
                        Prospect.linkedin_id.in_(\
                        tuple(self.json.get("boosted_ids")))).all()
                for prospect in extra_prospects:
                    user = {}
                    user['prospect_name'] = prospect.name
                    user['current_location'] = prospect.location_raw
                    user['current_industry'] = prospect.industry_raw
                    user['url'] = prospect.url
                    user['score'] = "N/A"
                    user['id'] = prospect.id
                    user['image_url'] = prospect.image_url if prospect.image_url else "/static/img/profile.png"
                    current_job = prospect.current_job
                    if current_job:
                        user['start_date'] = current_job.start_date.strftime("%y") if current_job.start_date else None
                        user['end_date'] = current_job.end_date.strftime("%y") if current_job.end_date else None
                        user['title'] = current_job.title
                        user['company_name'] = current_job.company.name
                        user['company_id'] = current_job.company_id
                        user['relationship'] = current_job.company.name
                    profiles.append(user)
                return profiles
        return []

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
            "wealthscore": self.wealthscore}
        if not no_fk:
            data['jobs'] = [job.to_json for job in self.jobs]
            data['current_job'] = "{}, {}".format(uu(self.current_job.title),\
                                        uu(self.current_job.company.name)) if self.current_job \
                                        else "N/A"
            data['schools'] = [school.to_json for school in self.schools]
            data['wealthscore'] = self.wealthscore
            #data["news"] =  self.relevant_content
        return data



    def __repr__(self):
        return '<Prospect id={0} url={1}>'.format(self.id, self.url)


class Location(db.Model):
    __tablename__ = "location"

    id = db.Column(BigInteger, primary_key=True)
    name = db.Column(String(1024))
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
    def get_url(self):
        return "/company/{}".format(self.company.id)

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                self.company.name,
                self.prospect.name
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

"""
class ProspectList(db.Model):
    __tablename__ = "prospect_list"

    id = db.Column(Integer, primary_key=True)
    prospect_ids = db.Column(Text)

    def __repr__(self):
        return '<ProspectList id={0}>'.format(
                self.id
                )
"""
