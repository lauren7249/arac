import json
import logging
import re
import requests
import lxml.html

from service import Service, S3SavedRequest

class GlassdoorService(Service):
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
        jobs = person.get("linkedin_data").get("experiences")
        for job in jobs:
            if job.get('end_date') == "Present":
                return job
        if len(jobs) > 0:
            return jobs[0]
        return None

    def process(self):
        self.logger.info('Starting Process: %s', 'Glass Door Service')
        for person in self.data:
            current_job = self._current_job(person)
            if current_job:
                request = GlassdoorRequest(current_job.get("title"))
                salary = request.process()
                if salary:
                    person.update({"glassdoor_salary": salary})
                    self.logger.info('Salary Found: %s', salary)
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Glass Door Service')
        return self.output


class GlassdoorRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
    """

    def __init__(self, query, type='email'):
        url =  "http://www.glassdoor.com/Salaries/"
        self.query = query.replace(" ",'-').strip()
        query_string = "-salary-SRCH_KO0," + str(len(self.query)) + ".htm"
        self.url = "".join([url, self.query, query_string])
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def process(self):
        self.logger.info('Glassdoor Request: %s', 'Starting')
        try:
            response = self._make_request()
            clean = lxml.html.fromstring(response)
            salary = clean.xpath("//div[@class='meanPay nowrap positive']")[0].text_content()
            salary = int(re.sub('\D','', salary))
        except Exception, e:
            salary = None
        return salary



