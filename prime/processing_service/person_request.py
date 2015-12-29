import hashlib
import logging
import requests
import boto
import dateutil
import datetime
from boto.s3.key import Key
import re
from helper import uu
from constants import AWS_KEY, AWS_SECRET, AWS_BUCKET, GLOBAL_HEADERS, CODER_ALIASES
from services.linkedin_query_api import get_person, get_people_viewed_also
from pipl_request import PiplRequest

DEFAULT_DATE = dateutil.parser.parse('January 1')

class PersonRequest(object):

    def __init__(self):
        pass

    def _get_current_job_from_experiences(self, linkedin_data):
        """
        Helper method useful on several child services
        """
        if linkedin_data and linkedin_data.get("experiences"):
            jobs = linkedin_data.get("experiences")
            current_job =filter(lambda x:x.get("end_date") == "Present", jobs)
            if len(current_job) == 1:
                return current_job[0]
            present_jobs = [job for job in jobs if job.get("end_date") is None]
            if len(present_jobs):
                start_date_jobs = [job for job in present_jobs if job.get("start_date")]
            else:
                start_date_jobs = [job for job in jobs if job.get("start_date")]
            if len(start_date_jobs) == 0:
                return jobs[0]
            return sorted(start_date_jobs, key=lambda x:dateutil.parser.parse(x.get("start_date"), default=DEFAULT_DATE), reverse=True)[0]
        return {}

    def is_programmer(self, linkedin_data):
        programmer_points = 0
        current_job = self._current_job_linkedin(linkedin_data)
        # if not current_job:
        #     return False
        title = current_job.get("title","")
        # if not title:
        #     return False
        title = re.sub("[^a-z\s]","", title.lower())
        # if not title:
        #     return False
        for alias in CODER_ALIASES:
            if title.find(alias)>-1:
                programmer_points+=1       

 
    def _current_job_linkedin(self, linkedin_data):
        job = {}
        current_job = self._get_current_job_from_experiences(linkedin_data)
        if current_job.get("end_date") == "Present":
            return current_job
        end_date = dateutil.parser.parse(current_job.get("end_date")) if \
        current_job.get("end_date") else None
        if not end_date or end_date.date() >= datetime.date.today():
            return current_job
        if linkedin_data.get("headline"):
            headline = linkedin_data.get("headline")
            if headline.find(" at "):
                job["title"] = headline.split(" at ")[0]
                job["company"] = " at ".join(headline.split(" at ")[1:])
            else:
                job["title"] = headline
            return job
        return job

    def _current_job(self, person):
        current_job = {}
        current_job = self._current_job_linkedin(person.get("linkedin_data",{}))
        if current_job:
            return current_job
        if person.get("job_title"):
            current_job = {"title": person.get("job_title"), "company": person.get("company")}
        return current_job

    def _get_linkedin_url(self, person):
        try:
            return person.values()[0]["linkedin_urls"]
        except:
            return person.values()[0]["source_url"]

    def _get_profile_by_any_url(self,url):
        profile = get_person(url=url)
        if profile:
            return profile
        request = PiplRequest(url, type="url", level="social")
        pipl_data = request.process()
        profile_linkedin_id = pipl_data.get("linkedin_id")
        profile = get_person(linkedin_id=profile_linkedin_id)
        return profile

    def _get_associated_profiles(self, linkedin_data):
        if not linkedin_data:
            return []
        source_url = linkedin_data.get("source_url")
        linkedin_id = linkedin_data.get("linkedin_id")
        if not source_url or not linkedin_id:
            return []
        also_viewed_urls = linkedin_data.get("urls",[])
        also_viewed = []
        for url in also_viewed_urls:
            profile = self._get_profile_by_any_url(url)
            if profile:
                also_viewed.append(profile)            
        viewed_also = get_people_viewed_also(url=source_url)
        if len(viewed_also) == 0:
            request = PiplRequest(linkedin_id, type="linkedin", level="social")
            pipl_data = request.process()
            new_url = pipl_data.get("linkedin_urls")
            viewed_also = get_people_viewed_also(url=new_url)
        return also_viewed + viewed_also
