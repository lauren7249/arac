import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest
from bing_request import BingRequestMaker
from constants import GLOBAL_HEADERS
from helper import get_domain
from person_request import PersonRequest
from helpers.stringhelpers import domestic_area

def wrapper(person):
    try:
        company_website = person.get("company_website")
        company_domain = get_domain(company_website)
        request = BloombergRequest(None)
        phone = request._get_phone_from_website(company_domain)   
        if phone:
            person["phone_number"]= phone
        else:
            company = PersonRequest()._current_job(person).get("company")
            phone, website = request._get_phone_from_name(company, company_domain)
            if phone:
                person["phone_number"]= phone
            if website:
                person["company_website"] = website    
        return person
    except Exception, e:
        print __name__ + str(e)
        return person        

class BloombergPhoneService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be existig data enriched with bloomberg phone numbers
    """

    def __init__(self, data, *args, **kwargs):
        super(BloombergPhoneService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        self.pool_size=20
        
class BloombergRequest(S3SavedRequest):

    """
    Given a company name, this will return the bloomberg company snapshot
    """

    def __init__(self, company, query_type="bloomberg_company"):
        self.company = company
        self.query_type = query_type
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.urls = []
        self.index = 0
        super(BloombergRequest, self).__init__()

    def _get_phone_from_website(self, company_domain):
        if not company_domain:
            return None
        self.company = company_domain.split(".")[0]
        self.query_type = "bloomberg_website"
        while self.has_next_url():
            data = self.process_next()
            phone = data.get("phone")
            website = data.get("website")
            #if we already know the website and it does not match, keep trying other bloomberg pages
            if website and company_domain == get_domain(website) and domestic_area(phone): 
                return phone
        return None   

    def _get_phone_from_name(self, company, company_domain):
        phone = None
        website = None
        if not company:
            return phone, website
        self.company = company
        self.query_type = "bloomberg_company"
        while self.has_next_url():
            data = self.process_next()
            phone = data.get("phone")
            website = data.get("website")
            #if we already know the website and it does not match, keep trying other bloomberg pages
            if company_domain and website and company_domain != get_domain(website): 
                phone = None
                website = None
                continue
            #found phone and website matches, we are done
            if phone:
                return phone, website
        return phone, website 

    def _get_urls(self):
        if self.urls:
            return
        self.bing = BingRequestMaker(self.company, self.query_type)
        self.urls = self.bing.process()

    def has_next_url(self):
        self._get_urls()
        if self.index < len(self.urls):
            return True
        return False

    def process_next(self):
        if self.has_next_url():
            self.url = self.urls[self.index]
            self.index +=1
            self.logger.info('Bloomberg Info Request: %s', 'Starting')
            self.html = self._make_request()
            info = self.parse_company_snapshot(self.html)
            return info
        return {}

    def process(self):
        info = self.process_next()
        return info

    def parse_company_snapshot(self,content):
        try:
            raw_html = lxml.html.fromstring(content)
        except:
            return {}
        try:
            name = raw_html.find(".//*[@itemprop='name']").text_content()
        except:
            name = None
        try:
            phone = raw_html.find(".//*[@itemprop='telephone']").text_content()
        except:
            phone = None
        try:
            address = "\n".join([e.text_content() for e in raw_html.xpath(".//*[@itemprop='address']/*")])
        except:
            address = None
        try:
            foundingDate = raw_html.find(".//*[@itemprop='foundingDate']").text_content()
        except:
            foundingDate = None
        try:
            website = raw_html.find(".//*[@itemprop='url']").get("href")
        except:
            website = None
        try:
            description = raw_html.find(".//*[@itemprop='description']").text_content()
        except:
            description = None
        fax = None
        employee_count = None
        try:
            detailsText = raw_html.find(".//*[@id='detailsContainer']").text_content()
            if re.search('(?<=Fax:\s)\S+',detailsText):
                fax = re.search('(?<=Fax:\s)\S+',detailsText).group(0)
            detailsText = "\n".join([e.text_content() for e in raw_html.xpath(".//*[@id='detailsContainer']/div/div/p")])
            if re.search('\S+(?=\sEmployees)',detailsText):
                employee_count = re.search('\S+(?=\sEmployees)',detailsText).group(0)
        except:
            pass
        keyExecutives = []
        for officer in raw_html.xpath(".//*[@class='officerOuter']"):
            member = officer.find(".//*[@itemprop='member']")
            memberName = member.text_content()
            gender = None
            if len(memberName.split(" "))>1:
                personalTitle = re.sub('[^a-z]','',memberName.split(" ")[0].lower())
                memberName = " ".join(memberName.split(" ")[1:])
                if personalTitle in ['ms','mrs','miss']:
                    gender = "Female"
                elif personalTitle in ["mr"]:
                    gender = "Male"
            memberPage = "http://www.bloomberg.com/research/stocks/private/{}".format(member.get("href")) 
            details = officer.xpath(".//div/div")
            if len(details) > 1:
                title = details[1].text_content().strip()
            else:
                title = None
            memberText = officer.text_content()
            if re.search('(?<=Age: )\d+',memberText):
                age = int(re.search('(?<=Age: )\d+',memberText).group(0))
            else:
                age = None
            if re.search('(?<=Total Annual Compensation: )\S+',memberText):
                salary = re.search('(?<=Total Annual Compensation: )\S+',memberText).group(0)
            else:
                salary = None
            officerInfo = {"name": memberName, "url": memberPage, "title": title,"age":age,"salary":salary,"gender":gender}
            keyExecutives.append(officerInfo)
        news = []
        for newsItem in raw_html.xpath(".//*[@class='newsItem']"):
            if newsItem.find(".//*[@class='storyHeadline']"):
                headline = newsItem.find(".//*[@class='storyHeadline']").text_content()
            else:
                headline = None
            try:
                date = newsItem.find(".//*[@class='storyTimestamp']").text_content()
                date = dateutil.parser.parse(date)
                date = str(date).split(" ")[0]
            except:
                date = None
            if newsItem.find(".//p"):
                story = newsItem.find(".//p").text_content()
            else:
                story = None
            newsInfo = {"headline": headline,"date":date,"story":story}
            news.append(newsInfo)
        tables = raw_html.xpath(".//table")
        similarCompanies = []
        if len(tables):
            similarCompaniesTable = raw_html.xpath(".//table")[0]
            for item in similarCompaniesTable.xpath(".//tbody/tr"):
                if len(item.xpath(".//td"))<2: continue
                company = item.xpath(".//td")[0].text_content()
                region = item.xpath(".//td")[1].text_content()
                info = {"company":company,"region":region}
                similarCompanies.append(info)
        recentTransactions = []
        if len(tables)>1:
            recentTransactionsTable = raw_html.xpath(".//table")[1]
            for item in recentTransactionsTable.xpath(".//tbody/tr"):
                if len(item.xpath(".//td"))<2: continue
                company = item.xpath(".//td")[1].text_content()
                details = item.xpath(".//td")[0].text_content()
                details = re.sub('[\n\r]','\t',details).strip()
                details = re.sub('\s{2,}','\t',details)
                transaction = details.split("\t")[0]
                try:
                    date = details.split("\t")[1]
                    date = dateutil.parser.parse(date)
                    date = str(date).split(" ")[0]
                except:
                    date = None
                info = {"company":company,"date":date,"transaction":transaction}
                recentTransactions.append(info)
        return {
            "name": name,
            "phone": phone,
            "fax": fax,
            "address":address,
            "foundingDate": foundingDate,
            "website": website,
            "description": description,
            "employee_count": employee_count,
            "keyExecutives": keyExecutives,
            "news": news,
            "similarCompanies": similarCompanies,
            "recentTransactions": recentTransactions
        }





