import json
import logging
import re
import requests
import lxml.html

from service import Service, S3SavedRequest
from person_request import PersonRequest

def wrapper(person):
    try:
        linkedin_data = person.get("linkedin_data",{})
        current_job = PersonRequest()._current_job(person)
        if current_job:
            title = current_job.get("title")
            location = current_job.get("location")
            request = IndeedRequest(title, location)
            salary = request.process()
            if salary:
                person.update({"indeed_salary": salary})   
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class IndeedService(Service):
    """
    Expected input is JSON of Linkedin Data
    """

    def __init__(self, data, *args, **kwargs):
        super(IndeedService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        
class IndeedRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
    """

    def __init__(self, title, location):
        self.location = location
        self.title = title
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(IndeedRequest, self).__init__()

    def process(self):
        self.logger.info('Indeed Request: %s', 'Starting')
        if self.location:
            self.url =  "http://www.indeed.com/salary?q1=%s&l1=%s" % (self.title, \
                    self.location)
        else:
            self.url ="http://www.indeed.com/salary?q1=%s" % (self.title)        
        response = self._make_request()
        try:
            self.clean = lxml.html.fromstring(response)
            raw_salary = self.clean.xpath("//span[@class='salary']")[0].text
            salary = re.sub('\D','', raw_salary)
            if not salary:
                return None
            salary = int(salary)
        except Exception, e:
            salary = None
            self.logger.error(e)
        return salary




