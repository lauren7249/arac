import clearbit
import logging
import hashlib
import boto

from requests import HTTPError
from boto.s3.key import Key
from geoindex.geo_point import GeoPoint

from service import Service, S3SavedRequest
from linkedin_service_crawlera import LinkedinRequest
from geocode_service import MapQuestRequest

class LeadService(Service):
    """
    Expected input is JSON 
    Output is filtered to qualified leads only
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.location = None
        self.jobs = []
        self.schools = []
        self.salary_threshold = 35000
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
        client_location = person.get("location_coordinates", {}).get("latlng")
        if client_location:
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
        If Salary doesn't exist, we assume they are specialized and good to go
        """
        #TODO current job logic
        current_job = self._current_job(person)
        salary = max(person.get("glassdoor_salary", 0), \
                person.get("indeed_salary", 0))
        self.logger.info("Person: %s, Salary: %s, Title: %s", \
                person.get("linkedin_data").get("source_url"), salary, current_job.get("title"))
        if salary == 0:
            return True
        if salary > self.salary_threshold:
            return True
        return False

    def _get_self_jobs_and_schools(self):
        person = LinkedinRequest(self.user_linkedin_url).process()
        self.jobs = person.get("experiences")
        self.schools = person.get("schools")
        location_raw = person.get("location")
        self.location = MapQuestRequest(location_raw).process()

    def process(self):
        self.logger.info('Starting Process: %s', 'Lead Service')
        self._get_self_jobs_and_schools()
        for person in self.data:
            salary = self._filter_salaries(person)
            location = self._filter_same_locations(person)
            if salary and location:
                self.good_leads.append(person)
            else:
                self.bad_leads.append(person)
        self.logger.info('Good Leads: %s', len(self.good_leads))
        self.logger.info('Bad Leads: %s', len(self.bad_leads))
        self.logger.info('Ending Process: %s', 'Lead Service')
        return self.good_leads, self.bad_leads
