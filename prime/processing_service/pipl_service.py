import json
import logging
import multiprocessing

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
        self.output = pool.map(unwrap_process, items_array)
        pool.close()
        pool.join()
        self.logger.info('Ending MultiProcess: %s', 'Pipl Service')
        return self.output

    def process(self):
        self.logger.info('Starting Process: %s', 'Pipl Service')
        for person, info in self.data.iteritems():
            request = PiplRequest(person)
            data = request.process()
            self.output.append(data)
        self.logger.info('Ending Process: %s', 'Pipl Service')
        return self.output


class PiplRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query, type='email'):
        pipl_url = "http://api.pipl.com/search/v3/json/?key="
        #make sure we keep using the key at https://pipl.com/accounts/subscriptions/ labeled "social"
        pipl_key = "ml2msz8le74d4nno7dyk0v7c"
        json_format = "&pretty=true"
        self.api_url = "".join([pipl_url, pipl_key, json_format])
        self.query = query
        self.type = type
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PiplRequest, self).__init__()

    def _build_url(self):
        if self.type == 'email':
            url = self.api_url + "&email=" + self.query
        else:
            url = self.api_url + "&username=" + self.query + "@{}".format(self.type)
        self.url = url

    def _social_accounts(self, pipl_json):
        social_accounts = []
        for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
            if not record.get('@query_params_match',True) or not \
                    record.get("source") or not \
                    record.get("source").get("url") or \
                    record.get("source").get("@is_sponsored"):
                continue
            link = record.get("source").get("url")
            social_accounts.append(link)
        return social_accounts

    def _images(self, pipl_json):
        images = []
        for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
            if not record.get('@query_params_match',True): continue
            for image in record.get("images",[]):
                url = image.get("url")
                if url and url not in images and url.find("gravatar.com")==-1:
                    images.append(url)
        return images

    def _linkedin_url(self, social_accounts):
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        return None

    def process(self):
        self.logger.info('Pipl Request: %s', 'Starting')
        response = {}
        self._build_url()
        super(PiplRequest, self)._make_request()
        html = self._make_request()
        pipl_json = json.loads(html)
        social_accounts = self._social_accounts(pipl_json)
        images = self._images(pipl_json)
        linkedin_url = self._linkedin_url(social_accounts)
        data = {"social_accounts": social_accounts,
                "linkedin_urls": linkedin_url,
                "images": images}
        response[self.query] = data
        return response



