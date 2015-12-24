import clearbit
import logging
import hashlib
import boto
import re
from requests import HTTPError
from boto.s3.key import Key
from geoindex.geo_point import GeoPoint
from helper import uu, name_match
from constants import NOT_REAL_JOB_WORDS, EXCLUDED_COMPANIES
from service import Service
from saved_request import S3SavedRequest
from geocode_service import MapQuestRequest
from glassdoor_service import GlassdoorService
from indeed_service import IndeedService
from geocode_service import GeoCodingService
from person_request import PersonRequest

class LeadService(Service):
    """
    Expected input is JSON 
    Output is filtered to qualified leads only
    
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(LeadService, self).__init__(*args, **kwargs)
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

    def _filter_same_locations(self, person):
        latlng = self.location.get("latlng")
        geopoint = GeoPoint(latlng[0],latlng[1])
        lead_location = person.get("location_coordinates", {}).get("latlng")
        if lead_location:
            lead_geopoint = GeoPoint(lead_location[0], lead_location[1])
            miles_apart = geopoint.distance_to(lead_geopoint)
            self.logger.info("Location: %s Miles Apart: %s",
                    person.get("location_coordinates",{}).get("locality"), miles_apart)
            if miles_apart < self.location_threshhold:
                self.logger.info("Same Location")
                return True
        else:
            self.logger.info("No Location")
        return False

    def _filter_title(self, title):
        if not title:
            self.logger.info("No job title")
            return False
        for word in NOT_REAL_JOB_WORDS:
            regex = "(\s|^)" + word + "(,|\s|$)"
            if re.search(regex, title.lower()):
                self.logger.info(uu(title + " not a real job"))
                return False
        return True

    def _filter_salaries(self, person):
        """
        If Salary doesn't exist, we assume they are specialized and good to go
        """
        linkedin_data = person.get("linkedin_data",{})
        current_job = PersonRequest()._current_job(person)
        title = current_job.get("title")
        if not self._filter_title(title):
            return False
        salary = max(person.get("glassdoor_salary", 0), person.get("indeed_salary", 0))
        self.logger.info("Person: %s, Salary: %s, Title: %s", linkedin_data.get("full_name"), salary, title)
        if salary == 0:
            return True
        if salary > self.salary_threshold:
            return True
        return False

    def _get_qualifying_info(self):
        self.location = MapQuestRequest(self.client_data.get("location")).process()   
        data = self.data         
        service = GeoCodingService(self.client_data, data)
        data = service.multiprocess() 
        service = GlassdoorService(self.client_data, data)
        data = service.multiprocess()      
        service = IndeedService(self.client_data, data)  
        data = service.multiprocess()                  
        return data

    def _is_same_person(self, person):
        person_name = person.get("linkedin_data",{}).get("full_name")
        if not person_name:
            return False
        if name_match(person_name.split(" ")[0], self.client_data.get("first_name")) \
            and name_match(person_name.split(" ")[1], self.client_data.get("last_name")):
            self.logger.info("%s is ME", person_name)
            return True
        self.logger.info("%s is NOT ME", person_name)
        return False

    #TODO: make this more robust
    def _is_competitor(self, person):
        linkedin_data = person.get("linkedin_data",{})
        person_company = PersonRequest()._current_job(person).get("company")
        if not person_company:
            return False
        if person_company.strip() in EXCLUDED_COMPANIES:
            self.logger.info("%s is a competitor", person_company)
            return True
        self.logger.info("%s is NOT a competitor", person_company)
        return False

    def _valid_lead(self, person):
        salary = self._filter_salaries(person)
        location = self._filter_same_locations(person)
        same_person = self._is_same_person(person)        
        competitor = self._is_competitor(person)    
        return salary and location and not same_person and not competitor
        
    def process(self):
        self.logger.info('Starting Process: %s', 'Lead Service')   
        data = self._get_qualifying_info()         
        for person in data:
            if self._valid_lead(person):
                self.good_leads.append(person)
            else:
                self.bad_leads.append(person)
        self.logger.info('Good Leads: %s', len(self.good_leads))
        self.logger.info('Bad Leads: %s', len(self.bad_leads))
        self.logger.info('Ending Process: %s', 'Lead Service')
        return self.good_leads

    def multiprocess(self):
        return self.process()
