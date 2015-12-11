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
        super(GlassdoorService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def process(self):
        self.logger.info('Starting Process: %s', 'Glass Door Service')
        for person in self.data:
            current_job = self._current_job(person)
            if current_job:
                request = GlassdoorRequest(current_job.get("title"))
                salary = request.process()
                if salary:
                    person.update({"glassdoor_salary": salary})
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Glass Door Service')
        return self.output


class GlassdoorRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
    """

    def __init__(self, title):
        self.title = title
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        super(GlassdoorRequest, self).__init__()

    def process(self):
        if not self.title: 
            return -1
        self.url =  "http://www.glassdoor.com/Salaries/" +  self.title.replace(" ",'-').strip() + "-salary-SRCH_KO0," + str(len(self.title.strip())) + ".htm"
        try:
            response = self._make_request()
            clean = lxml.html.fromstring(response)
        except Exception, err:
            self.logger.error(err.message)
            return -1
        try:
            salary = clean.xpath("//div[@class='meanPay nowrap positive']")[0].text_content()
            return int(re.sub('\D','', salary))
        except Exception, err:
            listings = clean.xpath(".//span[@class='i-occ strong noMargVert ']")
            if not listings: 
                return -1
            common = None
            for listing in listings:
                text = re.sub('[^a-z]',' ', listing.text.lower())
                words = set(text.split())
                common = common & words if common else words
            if not common: 
                return -1
            new_title = " ".join([w for w in text.split() if w in common])
            if new_title.lower().strip() == self.title.lower().strip(): 
                return -1
            self.logger.info(self.title.encode('utf-8') + "-->" + new_title.encode('utf-8'))
            self.title = new_title
            return self.process()
        return -1



