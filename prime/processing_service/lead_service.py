import clearbit
import logging
import hashlib
import boto
import re
from requests import HTTPError
from boto.s3.key import Key
from geoindex.geo_point import GeoPoint
from helper import uu
from constants import NOT_REAL_JOB_WORDS
from service import Service
from saved_request import S3SavedRequest
from geocode_service import MapQuestRequest
from glassdoor_service import GlassdoorService
from indeed_service import IndeedService
from geocode_service import GeoCodingService

class LeadService(Service):
    """
    Expected input is JSON 
    Output is filtered to qualified leads only
    TODO: check that the person is not the agent
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
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
        current_job = self._current_job(person)
        title = current_job.get("title")
        if not self._filter_title(title):
            return False
        salary = max(person.get("glassdoor_salary", 0), \
                person.get("indeed_salary", 0))
        self.logger.info("Person: %s, Salary: %s, Title: %s", \
                person.get("linkedin_data",{}).get("source_url"), salary, title)
        if salary == 0:
            return True
        if salary > self.salary_threshold:
            return True
        return False

    def _get_qualifying_info(self):
        self.location = MapQuestRequest(self.client_data.get("location")).process()   
        data = self.data         
        service = GeoCodingService(self.client_data, data)
        data = service.process()        
        service = GlassdoorService(self.client_data, data)
        data = service.process()
        service = IndeedService(self.client_data, data)
        data = service.process()     
        return data

    def _filter_title(self, title):
        if not title:
            return False
        for word in NOT_REAL_JOB_WORDS:
            regex = "(\s|^)" + word + "(,|\s|$)"
            if re.search(regex, title.lower()):
                self.logger.info(uu(title + " not a real job"))
                return False
        return True

    def process(self):
        self.logger.info('Starting Process: %s', 'Lead Service')   
        self.data = self._get_qualifying_info() 
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
        return self.good_leads
