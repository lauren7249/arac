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

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def dispatch(self):
        pass

    def _current_job(self, person):
        #TODO need to add in more robust logic for current job, sorted on date
        #TODO if no job, check Linkedin CSV
        #TODO if no job check headline
        jobs = person.get("linkedin_data").get("experiences")
        for job in jobs:
            if job.get('end_date') == "Present":
                return job
        if len(jobs) > 0:
            return jobs[0]
        return None

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
                    self.logger.info('Salary Found: %s', salary)
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Indeed Service')
        return self.output


class IndeedRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
    """

    def __init__(self, title, location, type='email'):
        self.location = location
        self.title = title
        if self.location:
            self.url =  "http://www.indeed.com/salary?q1=%s&l1=%s" % (self.title, \
                    self.location)
        else:
            self.url ="http://www.indeed.com/salary?q1=%s" % (self.title)
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)


    def process(self):
        self.logger.info('Indeed Request: %s', 'Starting')
        try:
            response = self._make_request()
            clean = lxml.html.fromstring(response)
            raw_salary = clean.xpath("//span[@class='salary']")[0].text
            salary = int(re.sub('\D','', raw_salary))
        except Exception, e:
            salary = None
        return salary




