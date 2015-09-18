import string
import random
import datetime
import json
import requests
import lxml.html
import os, re, json, numpy
from prime.utils import headers, get_bucket
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text, BigInteger, Float, TIMESTAMP, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSON, TSVECTOR, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL
from prime import db
from prime.prospects.helper import BingSearch
from citext import CIText
from prime.prospects.get_prospect import session
import dateutil.parser
from boto.s3.key import Key
from consume.facebook_consumer import *
from consume.api_consumer import *

bucket = get_bucket('facebook-profiles')

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

    id = db.Column(Integer, primary_key=True)

    url = db.Column(String(1024), index=True)
    name = db.Column(String(1024))
    linkedin_id = db.Column(String(1024), index=True)

    location = db.Column(Integer)
    location_raw = db.Column(String)

    image_url = db.Column(String(1024))

    industry = db.Column(Integer, ForeignKey("industry.id"))
    industry_raw = db.Column(String(1024))

    s3_key = db.Column(String(1024), index=True)
    complete = db.Column(Boolean)
    updated = db.Column(Date, index=True)
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
    def get_pipl_response(self) :
        content = {}
        if self.pipl_response: 
            content = self.pipl_response      
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
    def get_location(self):
        location = self.location_raw   
        if location: return location
        locations = get_pipl_locations(self.get_pipl_response)
        if len(locations): location = locations[0]
        return location

    @property
    def social_accounts(self):
        s = []
        pipl_response = self.get_pipl_response
        pipl_social_accounts = get_pipl_social_accounts(pipl_response)

        vibe_json = self.json.get("vibe") if self.json else {}
        vibe_social_accounts = get_vibe_social_accounts(vibe_json)

        for link in pipl_social_accounts + vibe_social_accounts:
            if link.find('linkedin.com') > -1 or type(link) is dict or link in s: continue
            s.append(link)  
        return s

    @property
    def email(self):
        if self.json:
            return self.json.get("email")
        return None

    @property
    def email_accounts(self):
        pipl_response = self.get_pipl_response
        return get_pipl_emails(pipl_response)

    @property
    def email_contacts(self):
        if self.json:
            return self.json.get("email_contacts")
        return None  

    @property
    def pipl_info(self):
        info = {}
        content = self.get_pipl_response
        if content:
            emails = content.get('person').get("emails")
            images = content.get('person').get("images")
            if len(emails) > 0:
                info['email'] = emails[0].get("address")     
        return info

    @property
    def find_pipl(self):
        try:
            pipl_info = self.pipl_info
            email = pipl_info.get("email")
            return email
        except:
            return None

    @property
    def calculate_salary(self):
        if self.current_job:
            return get_indeed_salary(self.current_job.title, location=self.location_raw)
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

    @property 
    def build_profile(self):
        image_url = self.image_url
        if not image_url:
            other_images = get_pipl_images(self.get_pipl_response)
            if len(other_images): image_url = other_images[0]
        profile = {"id":self.id, "name":self.name, "job": self.current_job.title if self.current_job and self.current_job.company else None, "company":self.current_job.company.name if self.current_job and self.current_job.company else None, "image_url":  image_url, "url":self.url, "linkedin": self.url}
        for link in self.social_accounts: 
            domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0]
            if domain in social_domains: profile.update({domain:link})
        return profile

    def __repr__(self):
        return '<Prospect id={0} url={1}>'.format(self.id, self.url)


class MapquestGeocodes(db.Model):
    __tablename__ = "mapquest_geocode"
    name = db.Column(CIText(), primary_key=True)
    geocode = db.Column(JSON)

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
    def get_indeed_salary(self):
        if self.indeed_salary:
            return self.indeed_salary
        self.indeed_salary = get_indeed_salary(self.title, location=self.location if self.location else self.prospect.location_raw)
        session.add(self)
        session.commit()
        return self.indeed_salary

    @property 
    def get_glassdoor_salary(self):
        if self.glassdoor_salary:
            return self.glassdoor_salary
        self.glassdoor_salary = get_glassdoor_salary(self.title)
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

class BingSearches(db.Model):
    __tablename__ = "bing_searches"

    terms = db.Column(CIText(), primary_key=True)
    site = db.Column(CIText(), primary_key=True)
    intitle = db.Column(CIText(), primary_key=True)
    inbody = db.Column(CIText(), primary_key=True)
    results = db.Column(JSON)
    pages = db.Column(Integer)
    next_querystring =db.Column(String(300))

    def __repr__(self):
        return '<Terms={0}, site={1}, intitle={2}, inbody={4}, pages={3}>'.format(
                self.terms,
                self.site,
                self.intitle,
                self.pages,
                self.inbody
                )


class GoogleProfileSearches(db.Model):
    __tablename__ = "google_profile_searches"

    terms = db.Column(CIText(), primary_key=True)
    name = db.Column(CIText(), primary_key=True)
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

class FacebookUrl(db.Model):
    __tablename__ = "facebook_urls"

    url = db.Column(CIText(), primary_key=True)
    username = db.Column(CIText, ForeignKey("facebook_contacts.facebook_id"), index=True)

    def __repr__(self):
        return '<url ={0} username={1}>'.format(
                self.url,
                self.username
                )

class ProspectUrl(db.Model):
    __tablename__ = "prospect_urls"

    url = db.Column(CIText(), primary_key=True)
    linkedin_id = db.Column(BigInteger)

    def __repr__(self):
        return '<url ={0} linkedin_id={1}>'.format(
                self.url,
                self.linkedin_id
                )

class FacebookContact(db.Model):
    __tablename__ = "facebook_contacts"

    facebook_id = db.Column(CIText(), primary_key=True)
    profile_info = db.Column(JSON)
    friends = db.Column(String(100))
    pipl_response = db.Column(JSON)
    fullcontact_response = db.Column(JSON)
    indeed_salary = db.Column(Integer)
    recent_engagers = db.Column(JSON)
    refresh = False

    def __repr__(self):
        return '<facebook_id ={0}>'.format(
                self.facebook_id
                )

    @property 
    def get_indeed_salary(self):
        salary = None
        if self.indeed_salary:
            return self.indeed_salary
        if not self.get_profile_info: return None
        if not self.get_profile_info.get("job_company") and not self.get_profile_info.get("job_title"): return None
        if self.get_profile_info.get("job_title") == "Worked": return None
        if self.get_profile_info.get("job_title") == "Works": 
            if not self.get_profile_info.get("job_company"): return None
            title = self.get_profile_info.get("job_company")
        elif not self.get_profile_info.get("job_company"): 
            title = self.get_profile_info.get("job_title") 
        else: 
            title = self.get_profile_info.get("job_title") + " at " + self.get_profile_info.get("job_company")
        salary = get_indeed_salary(title, location=self.get_profile_info.get("lives_in"))
        if not salary and self.get_profile_info.get("job_title") != "Works": 
            title = self.get_profile_info.get("job_title")
            salary = get_indeed_salary(title, location=self.get_profile_info.get("lives_in"))
        if not salary: salary = get_indeed_salary(title)
        if salary:
            self.indeed_salary = salary
            session.add(self)
            session.commit()
        return self.indeed_salary

    @property
    def get_friends(self):
        if self.friends: 
            return self.friends 
        key = Key(bucket)
        key.key = self.facebook_id + "-friends"
        if not key.exists(): return None
        source = key.get_contents_as_string() 
        friends = parse_facebook_friends(source)  
        self.friends = friends
        session.add(self)
        session.commit()
        return friends

    @property
    def get_pipl_response(self) :
        if self.pipl_response: 
            return self.pipl_response 
        content = {}
        try:
            url = pipl_url + "&username=" + self.facebook_id + "@facebook"
            response = requests.get(url)
            content = json.loads(response.content)    
            self.pipl_response = content     
            session.add(self)
            session.commit()                                        
        except:
            pass    
        return content 

    @property
    def get_fullcontact_response(self) :
        content = {}
        if self.fullcontact_response: 
            content = self.fullcontact_response
            return content      
        try:
            url = fullcontact_url + "&facebookUsername=" + self.facebook_id if not self.facebook_id.isdigit() else fullcontact_url + "&facebookId=" + self.facebook_id 
            response = requests.get(url)
            content = json.loads(response.content)
            if content.get("status") == 200:
                self.fullcontact_response = content     
                session.add(self)
                session.commit()                                        
        except:
            pass    
        return content 

    @property
    def social_accounts(self):
        s = []
        pipl_response = self.get_pipl_response
        pipl_social_accounts = get_pipl_social_accounts(pipl_response)

        fullcontact_response = self.get_fullcontact_response
        fullcontact_social_accounts = get_fullcontact_social_accounts(fullcontact_response)

        for link in pipl_social_accounts + fullcontact_social_accounts:
            if link.find('facebook.com') > -1 or type(link) is dict or link in s: continue
            s.append(link)  
        return s

    @property 
    def get_profile_source(self):
        key = Key(bucket)
        key.key = self.facebook_id
        if key.exists():
            return key.get_contents_as_string()     
        return None

    @property
    def top_engagers(self):
        top_engagers = set()
        engagers = self.get_recent_engagers
        if not engagers: return top_engagers
        for commenter in engagers.get("commenters",[]) + engagers.get("posters",[]):
            if commenter != self.facebook_id: top_engagers.add(commenter)
        for sublist in engagers.get("like_links",{}).values():
            for liker in sublist:
                if liker != self.facebook_id: top_engagers.add(liker) 
        return top_engagers

    @property 
    def get_recent_engagers(self):
        if self.recent_engagers:
            return self.recent_engagers
        source = self.get_profile_source
        engagers = parse_facebook_engagers(source)
        if engagers:
            self.recent_engagers = engagers
            session.add(self)
            session.commit()
        return engagers

    @property 
    def get_profile_info(self): 
        if self.profile_info and not self.refresh: return self.profile_info
        source = self.get_profile_source
        profile = parse_facebook_html(source)
        self.profile_info = profile     
        session.add(self)
        session.commit()          
        return profile

    @property 
    def get_location(self):
        profile_info = self.get_profile_info
        if not profile_info: return None
        location = profile_info.get("lives_in") if profile_info.get("lives_in") else profile_info.get("from")     
        if location: return location
        locations = get_pipl_cities(self.get_pipl_response)
        if len(locations): location = locations[0]
        return location

    @property 
    def build_profile(self):
        profile_info = self.get_profile_info
        image_url = profile_info.get("image_url")
        if not image_url:
            other_images = get_pipl_images(self.get_pipl_response)
            if len(other_images): image_url = other_images[0]        
        company = profile_info.get("job_company","").split("Past:")[0]
        facebook_url = "https://www.facebook.com/" + self.facebook_id
        profile = {"id":self.facebook_id, "name":profile_info.get("name"), "job": profile_info.get("job_title"), "company":company, "image_url": image_url, "url":facebook_url, "facebook":facebook_url, "school": profile_info.get("school_name"), "degree": profile_info.get("school_major")}
        for link in self.social_accounts: 
            domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0]
            if domain in social_domains: profile.update({domain:link})
        return profile

class EmailContact(db.Model):
    __tablename__ = "email_contacts"

    email = db.Column(CIText(), primary_key=True)
    linkedin_url = db.Column(String(150))
    pipl_response = db.Column(JSON)
    vibe_response = db.Column(JSON)
    fullcontact_response = db.Column(JSON)
    clearbit_response = db.Column(JSON)

    def __repr__(self):
        return '<email ={0} linkedin_url={1}>'.format(
                self.email,
                self.linkedin_url
                )

    @property 
    def get_clearbit_response(self):
        if self.clearbit_response: return self.clearbit_response
        person = clearbit.Person.find(email=self.email, stream=True)
        self.clearbit_response = person
        session.add(self)
        session.commit()
        return self.clearbit_response

    @property
    def get_pipl_response(self) :
        content = {}
        if self.pipl_response: 
            content = self.pipl_response      
        else:         
            try:
                url = pipl_url + "&email=" + self.email
                response = requests.get(url)
                content = json.loads(response.content)    
                self.pipl_response = content     
                session.add(self)
                session.commit()                                        
            except:
                pass    
        return content     

    @property
    def get_vibe_response(self) :
        content = {}
        if self.vibe_response: 
            content = self.vibe_response      
        else:         
            try:
                url = vibe_url + self.email
                response = requests.get(url)
                content = json.loads(response.content)    
                self.vibe_response = content     
                session.add(self)
                session.commit()                                        
            except:
                pass    
        return content  

    @property
    def get_fullcontact_response(self) :
        content = {}
        if self.fullcontact_response: 
            content = self.fullcontact_response
            return content      
        try:
            url = fullcontact_url + "&email=" + self.email
            response = requests.get(url)
            content = json.loads(response.content) 
            if content.get("status") == 200:   
                self.fullcontact_response = content     
                session.add(self)
                session.commit()                                        
        except:
            pass    
        return content 

    @property
    def social_accounts(self):
        s = []

        vibe_json = self.get_vibe_response
        if vibe_json.get("name") == 'Not a Person': return s
        vibe_social_accounts = get_vibe_social_accounts(vibe_json)

        pipl_response = self.get_pipl_response
        pipl_social_accounts = get_pipl_social_accounts(pipl_response)

        fullcontact_response = self.get_fullcontact_response
        fullcontact_social_accounts = get_fullcontact_social_accounts(fullcontact_response)

        for link in pipl_social_accounts + vibe_social_accounts + fullcontact_social_accounts:
            if type(link) is dict or link in s: continue
            s.append(link)  
        return s

class CloudspongeRecord(db.Model):
    __tablename__ = "cloudsponge_raw"
    id = db.Column(Integer, primary_key=True)
    user_email = db.Column(CIText())
    contacts_owner = db.Column(JSON)
    contact = db.Column(JSON)
    service = db.Column(CIText())

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



