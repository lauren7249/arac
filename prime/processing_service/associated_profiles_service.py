import logging
import requests

from service import Service
from constants import GLOBAL_HEADERS, in_profile_re, pub_profile_re
from services.linkedin_query_api import get_associated_profiles

class AssociatedProfilesService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existing data enriched with the profiles of people also viewed PLUS profiles in which the original person is in people also viewed
    TODO: make sure the profile is not the agent. need to change structure to include client linkedin id
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(AssociatedProfilesService, self).__init__(*args, **kwargs)

    def dedupe_profiles(self, profiles):
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

    def process(self):
        for person in self.data:
            linkedin_data = person.get("linkedin_data")
            associated_profiles = get_associated_profiles(linkedin_data)
            associated_profiles = self.dedupe_profiles(associated_profiles)
            if associated_profiles:
                person["associated_profiles"] = associated_profiles
            self.output.append(person)
        return self.output
