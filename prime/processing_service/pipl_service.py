import json
import logging
import time
import multiprocessing
from random import shuffle
from service import Service, S3SavedRequest

def unwrap_process(person):
    request = PiplRequest(person)
    return request.process()

class PiplService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts, images, and Linkedin IDs via PIPL
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PiplService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def multiprocess(self, poolsize=5):
        #pipl limits you to 20 hits/second. if you go above a pool size of 5, this could be an issue.
        self.logger.info('Starting MultiProcess: %s', 'Pipl Service')
        items_array = [person for person, info in self.data.iteritems()]
        pool = multiprocessing.Pool(processes=poolsize)
        self.results = pool.map(unwrap_process, items_array)
        pool.close()
        pool.join()
        for i in xrange(0, len(items_array)):
            self.output.append({items_array[i]:self.results[i]})
        self.logger.info('Ending MultiProcess: %s', 'Pipl Service')
        return self.output

    def process(self):
        self.logger.info('Starting Process: %s', 'Pipl Service')
        for person, info in self.data.iteritems():
            request = PiplRequest(person, type="email", level="social")
            data = request.process()
            self.output.append({person:data})
        self.logger.info('Ending Process: %s', 'Pipl Service')
        return self.output


class PiplRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query, type='email', level="social"):
        self.type = type
        self.json_format = "&pretty=true"
        pipl_url_v3 = "http://api.pipl.com/search/v3/json/?key="
        pipl_url_v4 = "http://api.pipl.com/search/v4/?key="
        #can be found at https://pipl.com/accounts/subscriptions/ 
        pipl_social_keys = ["ml2msz8le74d4nno7dyk0v7c"]
        pipl_profes_keys = ["uegvyy86ycyvyxjhhbwsuhj9","6cuq3648nfbqgch5verhcfte","z2ppf95933pmtqb2far8bnkd"]
        shuffle(pipl_social_keys)
        shuffle(pipl_profes_keys)
        if level == "social":
            self.pipl_key = pipl_social_keys[0]
        else:
            self.pipl_key = pipl_profes_keys[0]
        if self.type=="url":
            self.pipl_url = pipl_url_v4
            self.pipl_version = 4
        else:
            self.pipl_url = pipl_url_v3
            self.pipl_version = 3
        self.api_url = "".join([self.pipl_url, self.pipl_key, self.json_format])
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PiplRequest, self).__init__()

    def _build_url(self):
        if self.type == 'email':
            url = self.api_url + "&email=" + self.query
        elif self.type in ["facebook","linkedin"]:
            url = self.api_url + "&username=" + self.query + "@{}".format(self.type)
        elif self.type == "url":
            url = self.api_url + "&username=" + self.query 
        else:
            url = None
        self.url = url

    def _social_accounts(self, pipl_json):
        social_accounts = []
        if pipl_json is None:
            return social_accounts   
        if self.pipl_version == 3:     
            for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
                if not record.get('@query_params_match',True) or not \
                        record.get("source") or not \
                        record.get("source").get("url") or \
                        record.get("source").get("@is_sponsored"):
                    continue
                link = record.get("source").get("url")
                social_accounts.append(link)
        else:
            for record in pipl_json.get("person",{}).get("urls",[]):
                link = record.get("url")
                social_accounts.append(link)
        return social_accounts

    def _images(self, pipl_json):
        images = []
        if pipl_json is None:
            return images
        if self.pipl_version == 3:     
            for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
                if not record.get('@query_params_match',True): continue
                for image in record.get("images",[]):
                    url = image.get("url") 
                    if url and url not in images and url.find("gravatar.com")==-1: 
                        images.append(url)
        else:
            for record in pipl_json.get("person",{}).get("images",[]):
                url = record.get("url")
                if url and url not in images and url.find("gravatar.com")==-1: 
                    images.append(url)        
        return images

    def _linkedin_id(self, pipl_json):
        linkedin_id = None
        if self.pipl_version == 4:
            for record in pipl_json.get("person",{}).get("user_ids",[]):
                user_id = record.get("content")
                if not user_id or user_id.find("@linkedin") == -1:
                    continue
                linkedin_id = user_id.split("@")[0]
                if linkedin_id.isdigit():
                    return linkedin_id 
        else:
            for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
                if not record.get('@query_params_match',True): continue
                if record.get("source",{}).get("domain") != "linkedin.com": continue
                for user_id in record.get("user_ids",[]):
                    linkedin_id = user_id.get("content") 
                    if linkedin_id.isdigit():
                        return linkedin_id     
        return None

    def _linkedin_url(self, social_accounts):
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        return None

    def process(self):
        self.logger.info('Pipl Request: %s', 'Starting')
        self._build_url()
        if self.url is None:
            return {}      
        super(PiplRequest, self)._make_request()
        self.pipl_json = None
        tries = 0
        while self.pipl_json is None and tries<3:
            try:
                html = self._make_request()
                self.pipl_json = json.loads(html)
            except:
                time.sleep(1)
                pass
            tries+=1
        social_accounts = self._social_accounts(self.pipl_json)
        images = self._images(self.pipl_json)
        linkedin_id = self._linkedin_id(self.pipl_json)
        linkedin_url = self._linkedin_url(social_accounts)
        data = {"social_accounts": social_accounts,
                "linkedin_urls": linkedin_url, 
                "linkedin_id": linkedin_id,
                "images": images}
        return data



