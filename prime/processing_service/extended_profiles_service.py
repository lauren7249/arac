import logging
from service import Service
from constants import GLOBAL_HEADERS, in_profile_re, pub_profile_re
from helper import common_institutions

class ExtendedProfilesService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be array of extended profiles
    """

    #TODO: change input format to include user linkedin id instead of url https://developer.linkedin.com/docs/fields/contact
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
        extended_referrers = {}
        extended_profiles = []
        for person in self.data:
            person_profile = person.get("linkedin_data")
            associated_profiles = person.get("associated_profiles")
            if not associated_profiles:
                self.output.append(person)
                continue
            #extended_profiles = []
            for associated_profile in associated_profiles:
                commonality = common_institutions(person_profile, associated_profile)
                if not commonality:
                    continue
                referrers = extended_referrers.get(associated_profile.get("linkedin_id"),[])
                if len(referrers) == 0:
                    extended_profiles.append(associated_profile)
                referrer = {}
                referrer["referrer_connection"] = commonality
                referrer["referrer_id"] = person_profile.get("linkedin_id")
                referrer["referrer_url"] = person_profile.get("source_url")
                referrer["referrer_name"] = person_profile.get("name")
                referrers.append(referrer)
                extended_referrers[associated_profile.get("linkedin_id")] = referrers
            person.pop("associated_profiles")
            #person["extended_profiles"] = extended_profiles
            self.output.append(person)
        for extended_profile in extended_profiles:
            referrers = extended_referrers.get(extended_profile.get("linkedin_id"),[])
            extended_profile["referrers"] = referrers
            extended_profile["extended"] = True
            self.output.append(extended_profile)
        return self.output
