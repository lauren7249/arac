import clearbit
import logging
import hashlib
import boto

from requests import HTTPError
from boto.s3.key import Key
from geoindex.geo_point import GeoPoint

from service import Service
from saved_request import S3SavedRequest
from geocode_service import MapQuestRequest

class ExtendedLeadService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via PIPL
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        #we just want the good leads
        self.leads = data[0]
        self.location = None
        self.jobs = []
        self.schools = []
        self.salary_limit = 35000
        self.location_threshhold = 50
        self.good_leads = []
        self.bad_leads = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LeadService, self).__init__(*args, **kwargs)

    def _filter_same_locations(self, person):
        latlng = self.location.get("latlng")
        geopoint = GeoPoint(latlng[0],latlng[1])
        client_location = person.get("location_coordinates").get("latlng")
        client_geopoint = GeoPoint(client_location[0], client_location[1])
        miles_apart = geopoint.distance_to(client_geopoint)
        self.logger.info("Location: %s Miles Apart: %s",
                self.location.get("locality"), miles_apart)
        if miles_apart < self.location_threshhold:
            self.logger.info("Same Location")
            return True
        return False

    def _filter_salaries(self, person):
        """
        If Salary doesn't exist, we assume they specialized and good to go
        If they have been at their job for 3 years or more, they are good
        """
        #TODO current job logic
        current_job = self._current_job(person)
        salary = max(person.get("glassdoor_salary", 0), \
                person.get("indeed_salary", 0))
        self.logger.info("Person: %s, Salary: %s, Title: %s", \
                person.get("linkedin_data").get("source_url"), salary, current_job.get("title"))
        if salary == 0:
            return True
        if salary > self.salary_limit:
            return True
        return False

    def _get_self_jobs_and_schools(self):
        person = self._get_profile_by_any_url(self.user_linkedin_url)
        self.jobs = person.get("experiences")
        self.schools = person.get("schools")
        location_raw = person.get("linkedin_data").get("location")
        self.location = MapQuestRequest(location_raw).process()

    def process(self):
        pass

class BingProcessingService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via PIPL
    """

    def __init__(self, person, data, *args, **kwargs):
        self.person = person
        self.data = data
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BingProcessingService, self).__init__(*args, **kwargs)

    def _get_urls(self, name, headline, company_name, job_title):
        if headline:
            urls = set(bing.search_extended_network(name, school=headline))
        elif company_name:
            urls = set(bing.search_extended_network(name,
                school=company_name))
        else:
            urls = set(bing.search_extended_network(name,
                school=job_title))
        self.people_urls = set(urls + self.person.get("linkedin_data").get("urls"))
        return people_urls

    def _comonalities(self):
        pass

    def process(self):
        for person in self.data:
            headline = person.get("linkedin_data").get("headline")
            name = person.get("linkedin_data").get("full_name")
            current_job = self._current_job(person)
            company_name = current_job.get("company_name")
            job_title = current_job.get("job_title")
            people_urls = self._get_urls(name, headline, company_name,
                    job_title)
        return None

class BingNetworkRequest(S3SavedRequest):

    """
    WIP - to rework prime.utils.bing
    """
    def __init__(self, terms=None, site=None, intitle=None, inbody=None, limit=22, *args, **kwargs):
        self.name = urllib.quote('"{}"'.format(query))
        self.entity = urllib.quote('"{}"'.format(query))
        self.key = "Qk8G0Qg6Hq4TOCEhanrCrtol5cjw+9Ye0qrg+ls75oI"
        self.url = "https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?Query=%27" + self.query + "%27&$format=json"
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BingRequest, self).__init__(*args, **kwargs)

    def _clean_query(self):
        pass

    def process(self):
        self.logger.info('Clearbit Request: %s', 'Starting')
        response = {}
        response = self._build_request()
        json_result = json.loads(response.content)
        return json_result['d']['results']




