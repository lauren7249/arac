import logging
import requests

from service import Service
from constants import GLOBAL_HEADERS, in_profile_re, pub_profile_re
from services.linkedin_query_api import get_associated_profiles
from helper import common_institutions

class ExtendedProfilesService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existing data enriched with the extended profiles
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ExtendedProfilesService, self).__init__(*args, **kwargs)


    def process(self):
        for person in self.data:
            person_profile = person.get("linkedin_data")
            associated_profiles = person.get("associated_profiles")
            if not associated_profiles:
                self.output.append(person)
                continue
            extended_profiles = []
            for associated_profile in associated_profiles:
                commonality = common_institutions(person_profile, associated_profile)
                if not commonality:
                    continue
                associated_profile["commonality"] = commonality
                extended_profiles.append(associated_profile)
            person.pop("associated_profiles")
            person["extended_profiles"] = extended_profiles
            self.output.append(person)
        return self.output
