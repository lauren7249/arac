import hashlib
import datetime
import logging
import time
import sys
import os
import pandas
from helper import name_match
from prime.processing_service.service import Service
from prime.processing_service.constants import SOCIAL_DOMAINS

class ProfileBuilderService(Service):
    '''
    Add "profile" key to json for simplifying results service
    '''
    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.good_leads = data
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        self.industry_categories = pandas.read_csv('data/industries.csv', index_col='Industry', sep="\t").Category.to_dict()
        self.category_icons = pandas.read_csv('data/industry_icons.csv', index_col='Category', sep=",").Icon.to_dict()        
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ProfileBuilderService, self).__init__(*args, **kwargs)

    def _get_main_profile_image(self, images):
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

    def _get_social_fields(self, profile, social_accounts):
        if not profile: 
            profile = {}        
        if not social_accounts:
            return profile
        for link in social_accounts: 
            domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0].lower()
            if domain in SOCIAL_DOMAINS: 
                profile[domain] = link
        return profile 

    def _get_person_fields(self, profile, person):
        if not profile: 
            profile = {}        
        if not person:
            return profile
        latlng = person.get("location_coordinates",{}).get("latlng",[])
        if len(latlng)==2:
            profile["lat"] = latlng[0]
            profile["lng"] = latlng[1]
        profile["phone"] = person.get("phone_number")
        profile["wealthscore"] = person.get("wealthscore")
        print profile["wealthscore"]
        profile["age"] = person.get("age")
        profile["college_grad"] = person.get("college_grad")
        profile["gender"] = person.get("gender")
        profile["indeed_salary"] = person.get("indeed_salary")
        profile["glassdoor_salary"] = person.get("glassdoor_salary")
        profile["dob_min_year"] = person.get("dob_min")
        profile["dob_max_year"] = person.get("dob_max")
        profile["email_addresses"] = person.get("email_addresses")
        profile["profile_image_urls"] = person.get("images")
        profile["main_profile_image"] = self._get_main_profile_image(person.get("images"))
        profile["mailto"] = 'mailto:' + ",".join([x for x in person.get("email_addresses") if not x.endswith("@facebook.com")])        
        profile = self._get_social_fields(profile, person.get("social_accounts",[]))
        return profile

    def _get_linkedin_fields(self, profile, person):
        if not profile: 
            profile = {}
        data = person.get("linkedin_data")
        if not data:
            return profile
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
        profile["linkedin_url"] = data.get("source_url")   
        profile["linkedin_id"] = data.get("linkedin_id")   
        profile["main_profile_url"] = data.get("source_url")     
        profile["linkedin_name"] = data.get('full_name')
        profile["name"] = data.get('full_name')
        profile["linkedin_location_raw"] = data.get("location")
        profile["linkedin_industry_raw"] = data.get("industry")
        profile["linkedin_image_url"] = data.get("image")
        profile["linkedin_connections"] = connections
        profile["linkedin_headline"] = data.get("headline")
        profile["linkedin_json"] = new_data   
        #important that this is not named the name as the model fields because results service will throw an error
        profile["schools_json"] = data.get("schools")   
        profile["jobs_json"] = data.get("experiences")     
        return profile

    def _get_job_fields(self, profile, person):
        if not profile: 
            profile = {}        
        if not person:
            return profile
        current_job = self._current_job(person)
        profile['company'] = current_job.get("company")
        profile["job"] = current_job.get("title")
        return profile

    def _get_industry_fields(self, profile, person):
        if not profile: 
            profile = {}        
        if not person:
            return profile
        industry = person.get("company_industry") if person.get("company_industry") else profile.get("linkedin_industry_raw")
        profile["industry_category"] = self.industry_categories.get(industry)
        profile["industry_icon"] = self.category_icons.get(profile["industry_category"])
        return profile

    def _get_common_schools(self,profile):
        self._get_self_jobs_and_schools()
        agent_schools = set([school.get("college") for school in self.schools])
        prospect_schools = set([school.get("college") for school in profile.get("schools_json")])
        common_schools = set()
        for school1 in prospect_schools:
            for school2 in agent_schools:
                if name_match(school1,school2):
                    common_schools.add(school2)
        profile["common_schools"] = list(common_schools)
        return profile

    def process(self):
        self.logger.info('Starting Process: %s', 'Profile Builder Service')
        for person in self.good_leads:
            profile = {}
            profile = self._get_job_fields(profile, person)
            profile = self._get_linkedin_fields(profile, person)
            profile = self._get_person_fields(profile, person)
            profile = self._get_industry_fields(profile, person)
            profile = self._get_common_schools(profile)
            self.output.append(profile)
        self.logger.info('Ending Process: %s', 'Profile Builder Service')
        return self.output
