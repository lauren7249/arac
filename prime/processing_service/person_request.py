import hashlib
import logging
import requests
import boto
import datetime
from boto.s3.key import Key
import re
from helper import uu, parse_date
from constants import CODER_WORDS, PROGRAMMING_LANGUAGES, TECH_DEGREE_WORDS
from services.linkedin_query_api import get_person, get_people_viewed_also
from pipl_request import PiplRequest

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
            return sorted(start_date_jobs, key=lambda x:parse_date(x.get("start_date")) if parse_date(x.get("start_date")) else parse_date("Jan 1"), reverse=True)[0]
        return {}

    def programmer_points(self, linkedin_data):
        programmer_points = 0
        current_job = self._current_job_linkedin(linkedin_data)
        title = re.sub("[^a-z\s]","", current_job.get("title").lower()) if current_job.get("title") else ""
        description = re.sub("[^a-z\s]","", current_job.get("description").lower()) if current_job.get("description") else ""
        skills = linkedin_data.get("skills") if linkedin_data.get("skills") else []
        industry = linkedin_data.get("industry") if linkedin_data.get("industry") else ""
        summary = linkedin_data.get("summary") if linkedin_data.get("summary") else ""
        if industry in ["Computer Software",'Computer & Network Security','Information Technology and Services']:
            programmer_points+=2
        elif industry in ['Internet','Computer Networking']:
            programmer_points+=1
        for alias in CODER_WORDS:
            if title.find(alias)>-1:
                programmer_points+=3
            if description.find(alias)>-1:
                programmer_points+=1   
        for language in PROGRAMMING_LANGUAGES:
            if language in skills:
                programmer_points+=2
            if description.find(language)>-1:
                programmer_points+=1
            if summary.find(language)>-1:
                programmer_points+=1
        return programmer_points

    def has_technical_degree(self, linkedin_data):
        matched_before=None
        if not linkedin_data or not linkedin_data.get("schools"):
            return None
        for school in linkedin_data.get("schools",[]):
            #it's a high school so lets move on
            if school.get("college") and school.get("college").lower().find("high school") > -1:
                continue
            #still in school; hasnt earned degree
            if school.get("end_date") == "Present":
                continue
            #definitely a college degree if it's a bachelors
            if school.get("degree_type"):
                degree = school.get("degree_type")
            elif school.get("degree"):
                degree = school.get("degree")
            else:
                degree = None
            if not degree:
                continue  
            clean_degree = re.sub('[^0-9a-z\s]','',degree.lower().strip())
            if re.search('^(b(achelor(s)*( )+)*|m(aster(s)*( )+)*)( )*(of( )+)*(s(cience(s)*)*|e(ng(ineer(ing)*)*)*)($|\s)', clean_degree):
                if re.search('^(b(achelor(s)*( )+)*|m(aster(s)*( )+)*)( )*(of( )+)*s(cience(s)*)*($|\s)', clean_degree) and not re.search('^(b(achelor(s)*( )+)*|m(aster(s)*( )+)*)( )*(of( )+)*(e(ng(ineer(ing)*)*)*)($|\s)', clean_degree):
                    for word in TECH_DEGREE_WORDS:
                        if clean_degree.find(word)>-1:
                            return school
                else:
                    return school
            college = school.get("college") if school.get("college") else ""
            if school.get("college_id") or college.lower().find('university')>-1 or college.lower().find('college')>-1:
                start_date = parse_date(school.get("start_date"))
                end_date = parse_date(school.get("end_date"))
                #cant be a 4-year degree if you finished in less than 3 years
                if end_date and start_date and end_date.year - start_date.year < 3:
                    continue
                for word in TECH_DEGREE_WORDS:
                    if clean_degree.find(word)>-1:
                        return school
        # if matched_before:
        #     print "!!!!!!!!!!!!! " + matched_before.get("degree")
        return None

    def _current_job_linkedin(self, linkedin_data):
        job = {}
        current_job = self._get_current_job_from_experiences(linkedin_data)
        if current_job.get("end_date") == "Present":
            return current_job
        end_date = parse_date(current_job.get("end_date")) if current_job.get("end_date") else None
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

    def _get_profile(self, url=None, headline=None, name=None):
        if url:
            return self._get_profile_by_any_url(url)
        return get_person(headline=headline, name=name)
        
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
            new_url = pipl_data.get("linkedin_url")
            viewed_also = get_people_viewed_also(url=new_url)
        return also_viewed + viewed_also
