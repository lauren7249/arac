import hashlib
import datetime
import logging
import time
import sys
import os
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

    def _update_social_fields(self, profile, social_accounts):
        if not social_accounts or not profile:
            return profile
        for link in social_accounts: 
            domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0].lower()
            if domain in SOCIAL_DOMAINS: 
                profile[domain] = link
        return profile 

    def _update_person_fields(self, profile, person):
        if not person or not profile:
            return profile
        latlng = person.get("location_coordinates",{}).get("latlng",[])
        if len(latlng)==2:
            profile["lat"] = latlng[0]
            profile["lng"] = latlng[1]
        profile["phone"] = person.get("phone_number")
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
        profile = self._update_social_fields(profile, person.get("social_accounts",[]))
        return profile

    def _update_linkedin_fields(self, profile, data):
        if not profile or not data:
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
        profile["linkedin_name"] = data.get('full_name')
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

    def process(self):
        self.logger.info('Starting Process: %s', 'Profile Builder Service')
        for person in self.good_leads:
            data = person.get("linkedin_data")
            profile = {}
            profile = self._update_linkedin_fields(profile, data)
            profile = self._update_person_fields(profile, person)
            self.output.append(profile)
        self.logger.info('Ending Process: %s', 'Profile Builder Service')
        return self.output
