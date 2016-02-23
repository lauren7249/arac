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
from glassdoor_service import GlassdoorService
from indeed_service import IndeedService
from geocode_service import GeoCodingService, MapQuestRequest
from person_request import PersonRequest


class LeadService(Service):
    """
    Expected input is JSON 
    Output is filtered to qualified leads only
    
    """

    def __init__(self, data, *args, **kwargs):
        super(LeadService, self).__init__(data, *args, **kwargs)
        self.location = None
        self.jobs = []
        self.other_locations = []
        self.schools = []
        self.salary_threshold = 35000
        self.location_threshhold = 50
        self.user = self._get_user()  

    def _filter_same_locations(self, person):
        latlng = self.location.get("latlng")
        state = self.location.get("region")
        geopoint = GeoPoint(latlng[0],latlng[1])
        location_data = person.get("location_coordinates",{})
        lead_location =location_data.get("latlng")
        lead_state = location_data.get("region")
        if not lead_location:
            self.logger.info("No Location")
            person["reason"] = "No Location"
            person["step"] = "LeadService Location"
            self.excluded.append(person)                          
            return False            
        lead_geopoint = GeoPoint(lead_location[0], lead_location[1])
        miles_apart = geopoint.distance_to(lead_geopoint)
        self.logger.info("Location: {}, {} Miles Apart: {}".format(location_data.get("locality"),location_data.get("region"), miles_apart))
        if miles_apart < self.location_threshhold:
            self.logger.info("Same Location")
            return True
        if state == lead_state:
            self.logger.info("Same State")
            return True                
        for location in self.other_locations:
            latlng = location.get("latlng")
            geopoint = GeoPoint(latlng[0],latlng[1])                    
            miles_apart = geopoint.distance_to(lead_geopoint)
            self.logger.info("Location: {}, {} Miles Apart: {}".format(location_data.get("locality"),location_data.get("region"), miles_apart))
            if miles_apart < self.location_threshhold:
                self.logger.info("Same Location")
                return True             
    
        person["reason"] = "Not local -- Location: {}, {} Miles Apart: {}".format(location_data.get("locality"),location_data.get("region"), miles_apart)
        person["step"] = "LeadService Location"
        self.excluded.append(person)                
        return False

    def _filter_title(self, person):
        linkedin_data = person.get("linkedin_data",{})
        current_job = PersonRequest()._current_job(person)
        title = current_job.get("title")        
        if not title:
            #self.logger.info("No job title")
            person["reason"] = "No job title"
            person["step"] = "LeadService Job Title"
            self.excluded.append(person)                       
            return False
        for word in NOT_REAL_JOB_WORDS:
            regex = "(\s|^)" + word + "(,|\s|$)"
            if re.search(regex, title.lower()):
                person["reason"] = uu(title + " not a real job")
                person["step"] = "LeadService Job Title"
                self.excluded.append(person)                       
                #self.logger.info(uu(title + " not a real job"))
                return False
        return True

    def _filter_salaries(self, person):
        """
        If Salary doesn't exist, we assume they are specialized and good to go
        """
        if not self._filter_title(person):
            return False
        salary = max(person.get("glassdoor_salary", 0), person.get("indeed_salary", 0))
        #self.logger.info("Person: %s, Salary: %s, Title: %s", uu(linkedin_data.get("full_name")), salary, uu(title))
        if salary == 0:
            return True
        if salary > self.salary_threshold:
            return True
        person["reason"] = "Salary not high enough"
        person["step"] = "LeadService Job Salary"
        self.excluded.append(person)               
        return False

    def _get_qualifying_info(self):
        self.location = MapQuestRequest(self.client_data.get("location")).process()   
        for location in self.client_data.get("other_locations",[]):
            self.other_locations.append(MapQuestRequest(location).process())
        input_data = self.input_data         
        service = GeoCodingService(input_data)
        input_data = service.multiprocess() 
        service = GlassdoorService(input_data)
        input_data = service.multiprocess()      
        service = IndeedService(input_data)  
        input_data = service.multiprocess()                  
        return input_data.get("data",[])

    def _is_same_person(self, person):
        person_name = person.get("linkedin_data",{}).get("full_name")
        if not person_name:
            return False
        if name_match(person_name.split(" ")[0], self.client_data.get("first_name")) \
            and name_match(person_name.split(" ")[1], self.client_data.get("last_name")):
            #self.logger.info("%s is ME", uu(person_name))
            person["reason"] = "{} is same person as the Agent".format(uu(person_name))
            person["step"] = "LeadService Same Person"
            self.excluded.append(person)               
            return True
        return False

    #TODO: make this more robust
    def _is_competitor(self, person):
        linkedin_data = person.get("linkedin_data",{})
        person_company = PersonRequest()._current_job(person).get("company")
        if not person_company:
            return False
        if person_company.strip() in EXCLUDED_COMPANIES:
            person["reason"] = "{} is a competitor, or the same company".format(uu(person_company))
            person["step"] = "LeadService Competitor"   
            self.excluded.append(person)            
            #self.logger.info("%s is a competitor", uu(person_company))
            return True
        ##self.logger.info("%s is NOT a competitor", uu(person_company))
        return False

    def _valid_lead(self, person):
        same_person = self._is_same_person(person)   
        if same_person:
            return False          
        location = self._filter_same_locations(person)    
        if not location:
            return False     
        competitor = self._is_competitor(person)    
        if competitor:
            return False                             
        n_connections = person.get("linkedin_data",{}).get("connections","0")
        if n_connections and int(re.sub('[^0-9]','',n_connections))<10:
            person["reason"] = "{} is such a low number of connections, the profile did not seem real".format(n_connections)
            person["step"] = "LeadService n_connections"   
            self.excluded.append(person)                     
            return False
        salary = self._filter_salaries(person)
        return salary and location and not same_person and not competitor
        
    def process(self):
        self.logstart()
        try:
            data = self._get_qualifying_info()         
            for person in data:
                if self._valid_lead(person):
                    self.output.append(person)
            if self.user:
                self.user.generate_exclusions_report(self.excluded)                  
        except:
            self.logerror()
        self.logend()
        return {"data":self.output, "client_data":self.client_data}

    def multiprocess(self):
        return self.process()
