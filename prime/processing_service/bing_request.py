import logging
import hashlib
import boto
import lxml.html
import urllib
import json
import re
import sys
import dateutil
from requests import HTTPError
import requests
from random import shuffle
from boto.s3.key import Key
from constants import bing_api_keys
from service import S3SavedRequest
from constants import profile_re, bloomberg_company_re, school_re, company_re, plus_company_re
from helper import filter_bing_results, uu


class BingRequestMaker(S3SavedRequest):

    def __init__(self, name, type, extra_keywords=None, *args, **kwargs):
        self.name = name.replace('&','').replace(',','') if name else ""
        self.type = type
        self.extra_keywords = extra_keywords.replace('&','').replace(',','') if extra_keywords else None
        self.include_terms_in_title = None
        self.exclude_terms_from_title = None
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BingRequestMaker, self).__init__(*args, **kwargs)

    def _get_bing_request(self):
        if self.type == "linkedin_school":
            self.regex = school_re
            self.include_terms_in_title = self.name
            return BingRequest("", site="linkedin.com", intitle=['"' + re.sub(" ","+",self.name) + '"'], page_limit=22)
        elif self.type == "linkedin_company":
            self.regex = company_re
            self.include_terms_in_title = self.name
            return BingRequest("", site="linkedin.com", intitle=['"' + re.sub(" ","+",self.name) + '"'], page_limit=22)
        elif self.type == "bloomberg_company":
            self.regex = bloomberg_company_re
            self.include_terms_in_title = self.name
            return BingRequest("", site="bloomberg.com", intitle=['"' + re.sub(" ","+",self.name) + '"', '"Private Company Information - Businessweek"'], inbody=['"' + re.sub(" ","+",self.name) + '"'], page_limit=1)
        elif self.type == "bloomberg_website":
            self.regex = bloomberg_company_re
            self.include_terms_in_title = None
            return BingRequest("", site="bloomberg.com", intitle=['"Private Company Information - Businessweek"'], inbody=['"' + self.name + '"'], page_limit=1)            
        elif self.type == "linkedin_profile":
            self.regex = profile_re
            self.include_terms_in_title = self.name
            if self.extra_keywords and len(self.extra_keywords):
                inbody = '"' + self.extra_keywords + '"'
            else:
                inbody = ''
            return BingRequest("", site="linkedin.com", intitle=[self.name,'"| LinkedIn"'], inbody=[inbody], page_limit=22)
        elif self.type == "linkedin_extended_network":
            self.regex = profile_re
            self.exclude_terms_from_title = self.name
            inbody_name = '"' + self.name  + '"'
            if len(self.extra_keywords):
                inbody_school = '"' + self.extra_keywords + '"'
                inbody = [inbody_name, inbody_school]
            else:
                inbody = [inbody_name]
            return BingRequest("", site="linkedin.com", intitle=['"| LinkedIn"'], inbody=inbody, page_limit=22)
        else:
            return None

    def _process_results(self, results):
        filtered =  filter_bing_results(results, url_regex=self.regex, include_terms_in_title=self.include_terms_in_title, exclude_terms_from_title=self.exclude_terms_from_title)
        if self.type == "linkedin_school":
            school_ids = []
            for link in filtered:
                school_id = re.search("(?<=(\=|\-))[0-9]+", link)
                if not school_id: continue
                school_id = school_id.group(0)
                if school_id not in school_ids: school_ids.append(school_id)
            filtered = ["https://www.linkedin.com/edu/school?id=" + school_id for school_id in school_ids]
        elif self.type == "linkedin_company":
            urls = []
            for link in filtered:
                id = re.search('^https://www.linkedin.com/company/[a-zA-Z0-9\-]+(?=/)',link)
                if not id:
                    if link not in urls: urls.append(link)
                    continue
                id = id.group(0)
                if id not in urls: urls.append(id)
            filtered = urls
        return filtered

    def process(self):
        self.request_object = self._get_bing_request()
        self.results = self.request_object.process()
        clean_results = self._process_results(self.results)
        return clean_results

class BingRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via Clearbit
    """

    def __init__(self, terms, site="", intitle=[], inbody=[], page_limit=1):
        self.terms = urllib.urlencode(terms)
        self.site = site
        self.intitle = intitle
        self.inbody = inbody
        self.page_limit = page_limit
        self.pages = 0
        self.next_querystring = None
        self.results = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BingRequest, self).__init__()

    def _build_request(self):
        querystring = ""
        if len(self.terms): querystring += self.terms + " "
        if len(self.site): querystring += "site:" + self.site + " "
        if len(self.inbody):
            for ib in self.inbody:
                querystring += "inbody:" + ib + " "
        if len(self.intitle):
            for it in self.intitle:
                querystring += "intitle:" + it + " "
        try:
            self.querystring = urllib.quote(querystring)
        except:
            self.querystring = urllib.quote(uu(querystring))
        self.next_querystring = "https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?Query=%27" + self.querystring + "%27&Adult=%27Strict%27"


    def _make_request(self):
        shuffle(bing_api_keys)
        while self.next_querystring and self.pages<self.page_limit:
            for api_key in bing_api_keys:
                try:
                    html = self._get_html(api_key)
                    raw_results = json.loads(html.decode("utf-8-sig"))['d']
                    self.results += raw_results.get("results",[])
                    self.next_querystring = raw_results.get("__next")
                    self.pages+=1
                    break
                except:
                    if html:
                        self.logger.warn("Exception for bing request {} with the following response: {}".format(self.querystring, uu(html)))
                    else:
                        self.logger.warn("bing -- no response")
                if not self.next_querystring:
                    break
            if not self.next_querystring:
                break

    def _get_html(self, api_key):
        try:
            self.key = hashlib.md5(self.next_querystring).hexdigest()
        except:
            self.key = hashlib.md5(uu(self.next_querystring)).hexdigest()
        key = Key(self.bucket)
        key.key = self.key
        if key.exists():
            self.logger.info('Make Request: %s', 'Get From S3')
            html = key.get_contents_as_string()
            #only return if we didnt save a stupid error response from stupid bing like we were doing in the last stupid version of this function.
            try:
                raw_results = json.loads(html.decode("utf-8-sig"))['d']
                return html
            except:
                pass
        #guess that key didnt exist or the results were stupid
        try:
            response = requests.get(self.next_querystring + "&$format=json" , auth=(api_key, api_key))
            html = response.content
        except:
            html = None
        #at this point we have tried everything so better just leave it alone, return whatever crap we got and hope for the best.
        if html:
            try:
                #only save if it's not an error response from stupid bing.
                raw_results = json.loads(html.decode("utf-8-sig"))['d']            
                key.content_type = 'text/html'
                key.set_contents_from_string(html)
            except:
                pass
        return html

    def process(self):
        self.logger.info('Bing Request: %s', 'Starting')
        self._build_request()
        self._make_request()
        return self.results