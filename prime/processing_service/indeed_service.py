import json
import logging
import re
import requests
import lxml.html

from service import Service, S3SavedRequest

class IndeedService(Service):
    """
    Expected input is JSON of Linkedin Data
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(IndeedService, self).__init__(*args, **kwargs)

    def process(self):
        self.logger.info('Starting Process: %s', 'Indeed Service')
        for person in self.data:
            current_job = self._current_job(person)
            if current_job:
                title = current_job.get("title")
                location = current_job.get("location")
                request = IndeedRequest(title, location)
                salary = request.process()
                if salary:
                    person.update({"indeed_salary": salary})
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Indeed Service')
        return self.output


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
        self.clean = lxml.html.fromstring(response)
        try:
            raw_salary = self.clean.xpath("//span[@class='salary']")[0].text
            salary = int(re.sub('\D','', raw_salary))
        except Exception, e:
            salary = None
            self.logger.error(e.message)
        return salary




