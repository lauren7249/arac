import logging
from service import Service
from constants import GLOBAL_HEADERS, in_profile_re, pub_profile_re
from helper import common_institutions
from person_request import PersonRequest
import multiprocessing

def wrapper(person):
    person_profile = person.get("linkedin_data")
    associated_profiles = PersonRequest()._get_associated_profiles(person_profile)
    associated_profiles = Service()._dedupe_profiles(associated_profiles)
    return associated_profiles

class ExtendedProfilesService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be array of extended profiles
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(ExtendedProfilesService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.intermediate_output = []
        self.pool_size = 20
        self.wrapper = wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _collapse(self):
        extended_referrers = {}
        extended_profiles = []
        first_degree_linkedin_ids = set()
        for i in xrange(0, len(self.data)):
            associated_profiles = self.intermediate_output[i]
            person = self.data[i]
            person_profile = person.get("linkedin_data")
            linkedin_id = person_profile.get("linkedin_id")
            first_degree_linkedin_ids.add(linkedin_id)
            self.output.append(person)
            for associated_profile in associated_profiles:
                commonality = common_institutions(person_profile, associated_profile)
                if not commonality:
                    continue
                referrers = extended_referrers.get(associated_profile.get("linkedin_id"),[])
                if len(referrers) == 0:
                    extended_profiles.append({"linkedin_data":associated_profile})
                referrer = {}
                referrer["referrer_connection"] = commonality
                referrer["referrer_id"] = person_profile.get("linkedin_id")
                referrer["referrer_url"] = person_profile.get("source_url")
                referrer["referrer_name"] = person_profile.get("full_name")
                referrers.append(referrer)
                extended_referrers[associated_profile.get("linkedin_id")] = referrers
        for extended_profile in extended_profiles:
            extended_linkedin_id = extended_profile.get("linkedin_data",{}).get("linkedin_id")
            if extended_linkedin_id in first_degree_linkedin_ids:
                continue
            referrers = extended_referrers.get(extended_linkedin_id,[])
            extended_profile["referrers"] = referrers
            extended_profile["extended"] = True
            self.output.append(extended_profile)
        return self.output

    def multiprocess(self):
        self.logstart()
        try:
            self.pool = multiprocessing.Pool(self.pool_size)
            self.intermediate_output = self.pool.map(self.wrapper, self.data)
            self.pool.close()
            self.pool.join()
            self.output = self._collapse()
        except:
            self.logerror()
        self.logend()
        return self.output

    def process(self):
        self.logstart()
        try:
            for person in self.data:
                associated_profiles = self.wrapper(person)
                self.intermediate_output.append(associated_profiles)
            self.output = self._collapse()
        except:
            self.logerror()
        self.logend()
        return self.output
