import hashlib
import logging
import requests
import boto
from dateutil.parser import parser
import datetime
from boto.s3.key import Key

from constants import GLOBAL_HEADERS
import dateutil
from services.linkedin_query_api import get_person, get_people_viewed_also
from pipl_request import PiplRequest

from saved_request import S3SavedRequest

class Service(object):

    def __init__(self):
        pass

    def _dedupe_profiles(self, profiles):
        if not profiles:
            return []
        linkedin_ids = set()
        deduped = []
        for profile in profiles:
            id = profile.get("linkedin_id")
            if id in linkedin_ids:
                continue
            linkedin_ids.add(id)
            deduped.append(profile)
        return deduped

    def _get_self_jobs_and_schools(self):
        person = self._get_profile_by_any_url(self.client_data.get("url"))
        self.jobs = person.get("experiences")
        self.schools = person.get("schools")

    def _get_current_job_from_cloudsponge(self, person):
        for csv_person in self.data:
            for email in csv_person.get("email",[]):
                person_email = person.get("email", [{}])[0].get("address")
                if email.get("email", {}).get("address") == person_email:
                    if email.get("company"):
                        job["company"] = email.get("company")
                    if email.get("title"):
                        job["title"] = email.get("job_title")
                    return job
        return {}

    def _get_current_job_from_experiences(self, person):
        """
        Helper method useful on several child services
        """
        if person and person.get("linkedin_data", {}).get("experiences"):
            jobs = person.get("linkedin_data").get("experiences")
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
            return sorted(start_date_jobs, key=lambda x:dateutil.parser.parse(x.get("start_date")), reverse=True)[0]
        return {}

    def _current_job(self, person):
        job = {}
        current_job = self._get_current_job_from_experiences(person)
        if current_job.get("end_date") == "Present":
            return current_job
        end_date = dateutil.parser.parse(current_job.get("end_date")) if \
        current_job.get("end_date") else None
        if not end_date or end_date.date() >= datetime.date.today():
            return current_job
        current_job = self._get_current_job_from_cloudsponge(person)
        if current_job:
            return current_job
        if person.get("linkedin_data").get("headline"):
            headline = person.get("linkedin_data").get("headline")
            if headline.find(" at "):
                job["title"] = headline.split(" at ")[0]
                job["company"] = " at ".join(headline.split(" at ")[1:])
            else:
                job["title"] = headline
            return job
        return job

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



