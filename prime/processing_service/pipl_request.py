import json
import logging
import time
from random import shuffle
from saved_request import S3SavedRequest
from prime.processing_service.constants import PIPL_SOCIAL_KEYS, PIPL_PROFES_KEYS

class PiplRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query, type='email', level="social"):
        super(PiplRequest, self).__init__()
        self.type = type
        self.level = level
        self.json_format = "&pretty=true"
        pipl_url_v3 = "http://api.pipl.com/search/v3/json/?key="
        pipl_url_v4 = "http://api.pipl.com/search/v4/?key="
        shuffle(PIPL_SOCIAL_KEYS)
        shuffle(PIPL_PROFES_KEYS)
        if self.level == "social":
            self.pipl_key = PIPL_SOCIAL_KEYS[0]
        else:
            self.pipl_key = PIPL_PROFES_KEYS[0]
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
        

    def _build_url(self):
        if not self.query:
            return
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
        if not pipl_json:
            return None
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
        if not social_accounts:
            return None
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        return None

    def _emails(self, pipl_json):
        emails = []
        if not pipl_json: return emails
        for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
            if not record.get('@query_params_match',True) or not record.get("emails"): continue
            for email in record.get("emails",[]):
                url = email.get("address") 
                domain = url.split("@")[-1]
                if url and url not in emails and domain != 'facebook.com': 
                    emails.append(url)
        return emails  
        

    def get_emails(self):
        self.level = "email"
        self._build_url()
        if self.url is None:
            return {}
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
        emails = self._emails(self.pipl_json)
        return emails

    def process(self):
        self.logger.info('Pipl Request: %s', 'Starting')
        self._build_url()
        if self.url is None:
            return {}
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
        if self.level == "social":
            return data
        emails = self._emails(self.pipl_json)
        data["emails"] = emails
        return data



