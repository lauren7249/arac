import string
import random
import json
import requests
import lxml.html
import os, re
from prime.utils import headers
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text, BigInteger, Float, TIMESTAMP, ForeignKeyConstraint
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

    google_network_search = db.Column(JSON)
    pipl_response = db.Column(JSON) 

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
    def social_accounts(self):
        if self.json:
            vibe = self.json.get("vibe")
            if vibe:
                return vibe.get("social_profiles", [])
        return []


    @property
    def email(self):
        if self.json:
            return self.json.get("email")
        return None

    @property
    def email_contacts(self):
        if self.json:
            return self.json.get("email_contacts")
        return None  

    @property
    def pipl_info(self):
        info = {}
        if self.pipl_response: 
            content = self.pipl_response      
        else:
            try:
                base_url ="http://api.pipl.com/search/v3/json/?username="
                linkedin_id = str(self.linkedin_id)
                end_query = "@linkedin&key=uegvyy86ycyvyxjhhbwsuhj9&pretty=true"
                url = "".join([base_url, linkedin_id, end_query])
                response = requests.get(url)
                content = json.loads(response.content)                         
            except:
                pass
        if content:
            emails = content.get('person').get("emails")
            images = content.get('person').get("images")
            if len(emails) > 0:
                info['email'] = emails[0].get("address")
            if self.pipl_response is None:
                from prime.prospects.get_prospect import session
                self.pipl_response = content     
                session.add(self)
                session.commit()        
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
                boosted_ids = [int(id) for id in boosted_ids]
                extra_prospects = session.query(Prospect).filter(\
                        Prospect.linkedin_id.in_(boosted_ids)).all()
                for prospect in extra_prospects:
                    user = {}
                    user['prospect_name'] = prospect.name
                    user['current_location'] = prospect.location_raw
                    user['current_industry'] = prospect.industry_raw
                    user['url'] = prospect.url
                    user['score'] = "N/A"
                    user['id'] = prospect.id
                    user['wealthscore'] = prospect.wealthscore if prospect.wealthscore else random.choice([40, 55, 65, 86, 78])
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

    def wealth_percentile(self):
        if self.calculate_salary is None: return None
        salary = re.sub("[^0-9]","",self.calculate_salary)
        response = requests.get("http://www.whatsmypercent.com/incomeRank.php?income=" + salary + "&status=all%20filers", headers=headers)
        html = lxml.html.fromstring(response.content)
        percentile = html.xpath(".//td")[1].text_content()
        return int(re.sub("[^0-9]","",percentile))

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

class LinkedinSchool(db.Model):
    __tablename__ = "linkedin_schools"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100))
    pretty_url = db.Column(String(150))
    image_url = db.Column(String(300))

    def __repr__(self):
        return '<School id={0} name={1}>'.format(
                self.id,
                self.name
                )

class LinkedinCompany(db.Model):
    __tablename__ = "linkedin_companies"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100))
    pretty_url = db.Column(String(150))
    image_url = db.Column(String(300))

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

class GoogleProfileSearches(db.Model):
    __tablename__ = "google_profile_searches"

    terms = db.Column(String(300), primary_key=True)
    name = db.Column(String(200), primary_key=True)
    url = db.Column(String(200))

    def __repr__(self):
        return '<Terms={0} Name={1} url={2}>'.format(
                self.terms,
                self.name,
                self.url
                )

class ProxyDomainStatus(db.Model):
    __tablename__ = "proxy_domain_status"

    proxy_url = db.Column(String(30), ForeignKey("proxy.url"), primary_key=True, index=True)
    proxy = relationship('Proxy', foreign_keys='ProxyDomainStatus.proxy_url')
    domain = db.Column(String(100), primary_key=True)
    last_rejected = db.Column(TIMESTAMP)
    last_accepted = db.Column(TIMESTAMP)
    in_use = db.Column(Boolean)

    def __repr__(self):
        return '<Proxy={0} domain={1} last_rejected={2} last_accepted={3} in_use={4}>'.format(
                self.proxy_url,
                self.domain,
                self.last_rejected,
                self.last_accepted,
                self.in_use
                )

class ProxyDomainEvent(db.Model):
    __tablename__ = "proxy_domain_event"
    id = db.Column(Integer, primary_key=True)
    proxy_url = db.Column(String(30))
    domain = db.Column(String(100))
    event_time = db.Column(TIMESTAMP)
    status_code = db.Column(String(3))
    success = db.Column(Boolean)

    def __repr__(self):
        return '<Proxy={0} domain={1} event_time={2} status_code={3}> success={4}'.format(
                self.proxy_url,
                self.domain,
                self.event_time,
                self.status_code,
                self.success
                )

class ProspectUrl(db.Model):
    __tablename__ = "prospect_urls"

    url = db.Column(String(200), primary_key=True)
    linkedin_id = db.Column(BigInteger)

    def __repr__(self):
        return '<url ={0} linkedin_id={1}>'.format(
                self.url,
                self.linkedin_id
                )

class PiplEmail(db.Model):
    __tablename__ = "pipl_from_email"

    email = db.Column(String(200), primary_key=True)
    linkedin_url = db.Column(String(150))
    pipl_response = db.Column(JSON)

    def __repr__(self):
        return '<email ={0} linkedin_url={1}>'.format(
                self.email,
                self.linkedin_url
                )

class Proxy(db.Model):
    __tablename__ = "proxy"

    url = db.Column(String(30), primary_key=True)
    last_timeout = db.Column(TIMESTAMP)
    last_success = db.Column(TIMESTAMP)
    consecutive_timeouts = db.Column(Integer)

    def __repr__(self):
        return '<Proxy ={0} last_timeout={1} last_success={2} consecutive_timeouts={3}>'.format(
                self.url,
                self.last_timeout,
                self.last_success,
                self.consecutive_timeouts
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
