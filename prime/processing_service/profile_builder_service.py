import hashlib
import datetime
import logging
import time
import sys
import os
import pandas
from helper import name_match, sort_social_accounts
from service import Service, S3SavedRequest
from constants import SOCIAL_DOMAINS, INDUSTRY_CATEGORIES, CATEGORY_ICONS
from url_validator import UrlValidatorRequest
from person_request import PersonRequest

HIRED = False
AGENT_SCHOOLS = set()

def wrapper(person):
    request = ProfileBuilderRequest(person, HIRED)
    profile = request.process()
    profile = request._get_job_fields(profile, person)
    profile = request._get_common_schools(profile, AGENT_SCHOOLS)
    return profile

class ProfileBuilderService(Service):
    '''
    Add "profile" key to json for simplifying results service
    '''
    def __init__(self, client_data, data, *args, **kwargs):
        super(ProfileBuilderService, self).__init__(*args, **kwargs)
        self.data = data
        self.client_data = client_data
        self.data = data
        # global HIRED
        HIRED = self.client_data.get("hired")
        self.output = []
        self.wrapper = wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        person = PersonRequest()._get_profile_by_any_url(self.client_data.get("url"))
        schools = person.get("schools",[])
        AGENT_SCHOOLS = set([school.get("college") for school in schools])

class ProfileBuilderRequest(S3SavedRequest):

    """
    Builds profile in the best output format for results service
    """

    def __init__(self, person, hired):
        super(ProfileBuilderRequest, self).__init__()
        self.person = person
        self.profile = {}
        self.hired = hired
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_job_fields(self, profile, person):
        if not profile:
            profile = {}
        if not person:
            return profile
        current_job = PersonRequest()._current_job(person)
        profile['company'] = current_job.get("company")
        profile["job"] = current_job.get("title")
        return profile

    def _get_common_schools(self,profile, agent_schools):
        prospect_schools = set([school.get("college") for school in profile.get("schools_json",[])])
        common_schools = set()
        for school1 in prospect_schools:
            for school2 in agent_schools:
                if school1 and school2 and name_match(school1,school2):
                    common_schools.add(school2)
        profile["common_schools"] = list(common_schools)
        return profile

    def _get_main_profile_image(self):
        linkedin_image = self.person.get("linkedin_data",{}).get("image")
        if linkedin_image:
            _link = UrlValidatorRequest(linkedin_image, is_image=True).process()
            if _link:
                return _link
        images = self.person.get("images")
        if not images:
            return None
        best_person_score = 0.0
        best_profile_image = None
        for link, tags in images.iteritems():
            person_score = tags.get("person",0.0)
            if person_score>= best_person_score:
                best_person_score = person_score
                best_profile_image = link
        return best_profile_image

    def _get_social_fields(self, social_accounts):
        if not social_accounts:
            return self.profile
        social_accounts = sort_social_accounts(social_accounts)
        self.profile.update(social_accounts)
        self.profile["social_accounts"] = []
        for link in social_accounts.values():
            self.profile["social_accounts"].append(link)
        return self.profile

    def _get_person_fields(self):
        if not self.person:
            return self.profile
        latlng = self.person.get("location_coordinates",{}).get("latlng",[])
        if len(latlng)==2:
            self.profile["lat"] = latlng[0]
            self.profile["lng"] = latlng[1]
        self.profile["phone"] = self.person.get("phone_number")
        self.profile["company_website"] = self.person.get("company_website")
        self.profile["company_headquarters"] = self.person.get("company_headquarters")
        self.profile["age"] = self.person.get("age")
        self.profile["college_grad"] = self.person.get("college_grad")
        self.profile["gender"] = self.person.get("gender")
        self.profile["indeed_salary"] = self.person.get("indeed_salary")
        self.profile["glassdoor_salary"] = self.person.get("glassdoor_salary")
        self.profile["dob_min_year"] = self.person.get("dob_min")
        self.profile["dob_max_year"] = self.person.get("dob_max")
        if self.hired:
            self.profile["email_addresses"] = self.person.get("email_addresses")
            self.profile["profile_image_urls"] = self.person.get("images")
            self.profile["main_profile_image"] = self._get_main_profile_image()
            self.profile["mailto"] = 'mailto:' + ",".join([x for x in self.person.get("email_addresses",[]) if not x.endswith("@facebook.com")])
            self.profile["referrers"] = self.person.get("referrers",[])
            self.profile = self._get_social_fields(self.person.get("social_accounts",[]))
            self.profile["sources"] = self.person.get("sources",[])
        self.profile["extended"] = self.person.get("extended")
        return self.profile

    def _get_linkedin_fields(self):
        if not self.person:
            return self.profile
        data = self.person.get("linkedin_data")
        if not data:
            return self.profile
        new_data = {}
        new_data["skills"] = data.get("skills")
        new_data["groups"] = data.get("groups")
        new_data["projects"] = data.get("projects")
        new_data["people"] = data.get("people")
        new_data["interests"] = data.get("interests")
        new_data["causes"] = data.get("causes")
        new_data["organizations"] = data.get("organizations")
        connections = int(filter(lambda x: x.isdigit(), data.get("connections",
            0)))
        self.profile["linkedin_url"] = data.get("source_url")
        self.profile["linkedin_id"] = data.get("linkedin_id")
        self.profile["linkedin_name"] = data.get('full_name')
        self.profile["linkedin_location_raw"] = data.get("location")
        self.profile["linkedin_industry_raw"] = data.get("industry")
        self.profile["linkedin_image_url"] = data.get("image")
        self.profile["linkedin_connections"] = connections
        self.profile["linkedin_headline"] = data.get("headline")
        self.profile["linkedin_json"] = new_data
        #important that this is not named the name as the model fields because results service will throw an error
        self.profile["schools_json"] = data.get("schools")
        self.profile["jobs_json"] = data.get("experiences")
        self.profile["name"] = data.get('full_name')
        self.profile["main_profile_url"] = data.get("source_url")
        return self.profile

    def _get_industry_fields(self):
        if not self.person:
            return self.profile
        industry = self.person.get("company_industry") if self.person.get("company_industry") else self.profile.get("linkedin_industry_raw")
        self.profile["industry_category"] = INDUSTRY_CATEGORIES.get(industry)
        self.profile["industry_icon"] = CATEGORY_ICONS.get(self.profile["industry_category"])
        return self.profile

    def process(self):
        self.profile = self._get_linkedin_fields()
        self.profile = self._get_person_fields()
        self.profile = self._get_industry_fields()
        return self.profile
