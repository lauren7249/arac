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
            request = GlassdoorRequest(current_job.get("title"))
            salary = request.process()
            if salary:
                person.update({"glassdoor_salary": salary})   
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class GlassdoorService(Service):
    """
    Expected input is JSON of Linkedin Data
    """

    def __init__(self, data, *args, **kwargs):
        super(GlassdoorService, self).__init__(data, *args, **kwargs)
        self.pool_size = 20
        self.wrapper = wrapper
        
class GlassdoorRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
    """

    def __init__(self, title):
        self.title = title
        self.titles_tried = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        super(GlassdoorRequest, self).__init__()

    def process(self):
        if not self.title: 
            return -1
        self.titles_tried.append(self.title.lower().strip())
        self.url =  "http://www.glassdoor.com/Salaries/{}-salary-SRCH_KO0,{}.htm".format(self.title.replace(" ",'-').strip(), str(len(self.title.strip())))
        try:
            response = self._make_request()
            clean = lxml.html.fromstring(response)
        except Exception, err:
            self.logger.error(str(err))
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
            if new_title.lower().strip() in self.titles_tried: 
                return -1
            self.logger.info("{}-->{}".format(self.title.encode('utf-8'), new_title.encode('utf-8')))
            self.title = new_title
            return self.process()
        return -1



