import json
import unittest
import requests
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.testing import TestCase, LiveServerTestCase

from prime.processing_service.cloudsponge_service import CloudSpongeService
from prime.processing_service.clearbit_service_webhooks import ClearbitPersonService, ClearbitPhoneService
from prime.processing_service.pipl_service import PiplService, PiplRequest
from prime.processing_service.linkedin_service_crawlera import LinkedinService
from prime.processing_service.linkedin_company_service import LinkedinCompanyService
from prime.processing_service.glassdoor_service import GlassdoorService
from prime.processing_service.indeed_service import IndeedService
from prime.processing_service.bing_request import BingRequestMaker
from prime.processing_service.lead_service import LeadService
from prime.processing_service.bloomberg_service import BloombergRequest, BloombergPhoneService
from prime.processing_service.phone_service import PhoneService
from prime.processing_service.mapquest_request import MapQuestRequest
from prime.processing_service.geocode_service import GeoCodingService
from prime.processing_service.social_profiles_service import SocialProfilesService, UrlValidatorRequest
from prime.processing_service.gender_service import GenderService
from prime.processing_service.age_service import AgeService
from prime.processing_service.college_degree_service import CollegeDegreeService
from prime.processing_service.extended_profiles_service import ExtendedProfilesService
from prime import create_app, db
from config import config

class TestCloudspongeService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        client_data = {"email": email, "url":linkedin_url,"location":"New York, New York","first_name":"James", "last_name":"Johnson"}
        emails = [{"contact": {"email":[{"address": "jamesjohnson11@gmail.com"}]}},
                {"contact": {"email":[{"address": "jamesjohnson11@gmail.com"}]}}]
        self.service = CloudSpongeService(client_data, emails)

    def test_cloudsponge(self):
        expected = [{'jamesjohnson11@gmail.com': {'sources':[],'first_name': None, 'last_name':None, 'companies': None,'job_title': None}}]
        data = self.service.multiprocess()
        self.assertEqual(data, expected)

class TestCollegeDegreeService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_college(self):
        self.service = CollegeDegreeService(None, self.data)
        data = self.service.multiprocess()
        self.assertEqual(data[0].get("college_grad"), True)
        self.assertEqual(data[1].get("college_grad"), True)
        # self.service = CollegeDegreeService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestAgeService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = AgeService(None, data)

    def test_age(self):
        data = self.service.multiprocess()
        self.assertEqual(data[0].get("age"), 28.5)
        self.assertEqual(data[1].get("age"), 26.5)
        self.assertEqual(data[0].get("dob_min"), 1986)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestLeadService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        client_data = {"email": email, "url":linkedin_url,"location":"New York, New York","first_name":"James", "last_name":"Johnson"}
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = LeadService(client_data, data)
        self.data = self.service.multiprocess()
    def test_lead(self):
        self.assertEqual(len(self.data), 1)

class TestGeoCodingService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        self.client_data = {"email": email, "url":linkedin_url,"location":"New York, New York","first_name":"James", "last_name":"Johnson"}
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_geocode(self):
        expected = (40.713054, -74.007228)
        self.service = GeoCodingService(self.client_data, self.data)
        data = self.service.multiprocess()
        latlng = data[1].get("location_coordinates").get("latlng")
        self.assertEqual(latlng[0], expected[0])
        self.assertEqual(latlng[1], expected[1])
        # self.service = GeoCodingService(self.client_data, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestUrlValidatorRequest(unittest.TestCase):

    def test_url(self):
        url = 'https://media.licdn.com/mpr/mpr/shrinknp_400_400/AAEAAQAAAAAAAAKmAAAAJDI4YTRlZGJiLTE3ZDktNDBmNS04MmYwLWZlM2VmZThkNjllMg.jpg'
        req = UrlValidatorRequest(url, is_image=True)
        self.assertEqual(req.process(), None)
        url = 'http://graph.facebook.com/662395164/picture?type=large'
        req = UrlValidatorRequest(url, is_image=True)
        self.assertEqual(req.process(), 'https://public-profile-photos.s3.amazonaws.com/6231a637dc9c7dfc22577ecc11296f82')

class TestMapquestRequest(unittest.TestCase):
    def setUp(self):
        business_name = "emergence capital partners"
        location = "san francisco bay area"
        self.location_service = MapQuestRequest(location)
        self.business_service = MapQuestRequest(business_name)

    def test_mapquest(self):
        expected_phone = '(650) 573-3100'
        expected_website = 'http://emcap.com'
        latlng = self.location_service.process().get("latlng")
        business = self.business_service.get_business(latlng=latlng)
        phone = business.get("phone_number")
        website = business.get("company_website")
        self.assertEqual(phone, expected_phone)
        self.assertEqual(website, expected_website)


class TestPiplService(unittest.TestCase):

    def setUp(self):
        self.emails = [{"jamesjohnson11@gmail.com":{}}]

    def test_pipl_from_email(self):
        self.service = PiplService(None, self.emails)
        data1 = self.service.multiprocess()
        # self.service = PiplService(None, self.emails)
        #TODO multiprocess broken
        #data2 = self.service.multiprocess()
        self.assertEqual(data1[0].get("jamesjohnson11@gmail.com").get("social_accounts"), [u'http://www.linkedin.com/pub/james-johnson/a/431/7a0',
                u'https://plus.google.com/106226923266702208073/about'])
        #self.assertEqual(data1,data2)

    def test_pipl_from_username(self):
        request = PiplRequest("laurentracytalbot", type="facebook", level="social")
        data = request.process()
        self.assertEqual(data, {'images': [u'http://media.licdn.com/mpr/mpr/shrink_500_500/p/1/005/047/070/33fa685.jpg',
               u'http://graph.facebook.com/213344/picture?type=large',
               u'https://lh6.googleusercontent.com/-6z3fhsO9SQU/AAAAAAAAAAI/AAAAAAAAAAA/g2ihihLkzXM/photo.jpg'],
              'linkedin_id': u'75874081',
              'linkedin_urls': u'http://www.linkedin.com/pub/lauren-talbot/21/4b0/741',
              'social_accounts': [u'http://www.linkedin.com/pub/lauren-talbot/21/4b0/741',
               u'http://facebook.com/people/_/213344',
               u'https://plus.google.com/114331116808631299757/about']})

    def test_pipl_from_url(self):
        request = PiplRequest("http://www.linkedin.com/pub/gordon-ritter/1/b95/a97", type="url", level="social")
        data = request.process()
        self.assertEqual(data, {'images': [u'http://graph.facebook.com/552796269/picture?type=large',
                  u'http://media.licdn.com/mpr/mpr/p/1/000/002/275/3e677fb.jpg'],
                 'linkedin_id': u'5919955',
                 'linkedin_urls': u'http://www.linkedin.com/pub/gordon-ritter/1/b95/a97',
                 'social_accounts': [u'http://www.facebook.com/people/_/552796269',
                  u'http://www.linkedin.com/pub/gordon-ritter/1/b95/a97',
                  u'http://www.flickr.com/people/47088076@N06/',
                  u'http://www.facebook.com/gordon.ritter.92']})

class TestClearbitPersonService(unittest.TestCase):

    def setUp(self):
        self.emails = [{"alex@alexmaccaw.com":{"social_accounts":["boo"],"linkedin_urls":u'https://www.linkedin.com/in/alex-maccaw'}},{"laurentracytalbot@gmail.com":{}}]
        self.maxDiff = None

    def test_clearbit(self):
        # self.service = ClearbitPersonService(None, self.emails)
        # data1 = self.service.process()
        self.service = ClearbitPersonService(None, self.emails)
        data = self.service.multiprocess()
        self.assertEqual(data[0].get('alex@alexmaccaw.com').get("social_accounts"),
            ['boo', u'https://github.com/maccman', u'https://aboutme.com/maccaw',
            u'https://twitter.com/maccaw', u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
            u'https://gravatar.com/maccman', u'https://facebook.com/amaccaw', u'https://angel.co/maccaw'])
        self.assertEqual(data[0].get('alex@alexmaccaw.com').get("linkedin_urls"), u'https://www.linkedin.com/in/alex-maccaw')
        self.assertEqual(data[1].get('laurentracytalbot@gmail.com').get("gender"), 'female')
        # self.assertEqual(data1,data2)

class TestClearbitPhoneService(unittest.TestCase):

    def setUp(self):
        self.data = [{}]
        self.data[0]["company_website"] = "www.microsoft.com"

    def test_clearbit(self):
        expected_phone = '+1 425-882-8080'
        self.service = ClearbitPhoneService(None, self.data)
        data = self.service.multiprocess()
        phone = data[0].get("phone_number")
        self.assertEqual(phone, expected_phone)
        # self.service = ClearbitPhoneService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestBloombergRequest(unittest.TestCase):

    def setUp(self):
        name = "kpmg"
        self.service = BloombergRequest(name)

    def test_bloomberg(self):
        expected_phone = '212-758-9700'
        expected_website = 'http://www.kpmg.com/us'
        data = self.service.process_next()
        data = self.service.process_next()
        phone = data.get("phone")
        website = data.get("website")
        self.assertEqual(phone, expected_phone)
        self.assertEqual(website, expected_website)

class TestExtendedProfilesService(unittest.TestCase):

    def setUp(self):
        data = [{u'julia.mailander@gmail.com':
                {'linkedin_urls': u'https://www.linkedin.com/in/juliamailander',
                'social_accounts': [u'https://www.linkedin.com/in/juliamailander',\
                        u'https://plus.google.com/103608304178303305879/about']}
                }]
        li_service = LinkedinService(None, data)
        self.data = li_service.multiprocess()

    def test_extended(self):
        service = ExtendedProfilesService(None, self.data)
        data = service.multiprocess()
        extended = [profile for profile in data if profile.get("extended")]
        self.assertEqual(extended[0].get("referrers")[0].get("referrer_connection"), 'Worked at Emergence Capital together 2014-Present')
        # service = ExtendedProfilesService(None, self.data)
        # data = service.multiprocess()
        # self.assertEqual(data, data2)
        self.assertEqual(len(extended), 14)

class TestPhoneService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_phone(self):
        self.service = PhoneService(None, self.data)
        expected = '650-573-3100'
        data = self.service.multiprocess()
        phone = data[2].get("phone_number")
        self.assertEqual(phone, expected)
        # self.service = PhoneService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestBloombergPhoneService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = BloombergPhoneService(None, data)

    def test_bloomberg(self):
        data = self.service.multiprocess()
        self.assertEqual(data[1].get("phone_number"), '800-507-9396')
        self.assertEqual(data[2].get("phone_number"), '650-573-3100')
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestLinkedinCompanyService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_linkedin_company(self):
        self.service = LinkedinCompanyService(None, self.data)
        data = self.service.multiprocess()
        self.assertEqual(data[0].get("company_website"), 'http://vycapital.com')
        self.assertEqual(data[1].get("company_website"), 'http://www.farmivore.com')
        self.assertEqual(data[2].get("company_website"), 'http://www.emcap.com')
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestGenderService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_gender(self):
        self.service = GenderService(None, self.data)
        data = self.service.multiprocess()
        self.assertEqual(data[0].get("gender"), 'female')
        self.assertEqual(data[1].get("gender"), 'unknown')
        # self.service = GenderService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestLinkedinService(unittest.TestCase):

    def setUp(self):
        self.data = [{u'julia.mailander@gmail.com':
                {'linkedin_urls': u'https://www.linkedin.com/in/juliamailander',
                'social_accounts': [u'https://www.linkedin.com/in/juliamailander',\
                        u'https://plus.google.com/103608304178303305879/about']}
                },
                {u'julia.mailander2@gmail.com':
                {'linkedin_urls': u'http://www.linkedin.com/pub/julia-mailander/11/898/614',
                'social_accounts': [u'http://www.gravatar.com/5cb9f218a2e29a21ab19b3a524b3506d',u'https://plus.google.com/103608304178303305879/about']}
                }]


    def test_linkedin(self):
        self.service = LinkedinService(None, self.data)
        data = self.service.multiprocess()
        self.assertEqual(data[0].get("linkedin_data").get("urls"), [u'http://www.linkedin.com/pub/santi-subotovsky/0/2b2/6b0',
                     u'http://www.linkedin.com/pub/everett-cox/3/9b6/9b8',
                     u'http://www.linkedin.com/in/jeffweiner08',
                     u'http://www.linkedin.com/pub/brian-jacobs/0/a/7a6',
                     u'http://www.linkedin.com/pub/jason-green/1/22b/409',
                     u'http://www.linkedin.com/pub/john-chen/1b/215/b97',
                     u'http://www.linkedin.com/pub/alison-wagonfeld/0/669/829',
                     u'http://www.linkedin.com/pub/kate-berger/18/215/a01',
                     u'http://www.linkedin.com/pub/jake-saper/0/834/536',
                     u'http://www.linkedin.com/pub/joseph-floyd/2/8a4/55b',
                     u'http://www.linkedin.com/pub/gordon-ritter/1/b95/a97'])
        self.assertEqual(len(data),1)
        self.assertEqual(len(data[0].get("email_addresses")),2)
        self.assertEqual(len(data[0].get("social_accounts")),3)
        # self.service = LinkedinService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestGlassdoorService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_glassdoor(self):
        self.service = GlassdoorService(None, self.data)
        data = self.service.multiprocess()
        salary = data[0].get("glassdoor_salary")
        self.assertEqual(salary, 66565)
        # self.service = GlassdoorService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class TestIndeedService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_indeed(self):
        expected = 102000
        self.service = IndeedService(None, self.data)
        data = self.service.multiprocess()
        salary = data[0].get("indeed_salary")
        self.assertEqual(salary, expected)
        # self.service = IndeedService(None, self.data)
        # data2 = self.service.multiprocess()
        # self.assertEqual(data, data2)

class BingServiceLinkedinCompany(unittest.TestCase):

    def setUp(self):
        name = "vy capital"
        self.service = BingRequestMaker(name, "linkedin_company")

    def test_linkedin_company(self):
        expected = "https://www.linkedin.com/company/vy-capital"
        data = self.service.process()
        assert(expected in data)

class BingServiceBloombergCompany(unittest.TestCase):

    def test_bloomberg_company(self):
        self.service = BingRequestMaker("farmivore", "bloomberg_company")
        expected = "http://www.bloomberg.com/research/stocks/private/snapshot.asp?privcapId=262829137"
        data = self.service.process()
        assert(expected in data)
        self.service = BingRequestMaker("emergence capital partners", "bloomberg_company")
        expected = "http://www.bloomberg.com/research/stocks/private/snapshot.asp?privcapId=4474737"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinSchool(unittest.TestCase):

    def setUp(self):
        name = "marist college"
        self.service = BingRequestMaker(name, "linkedin_school")

    def test_linkedin_school(self):
        expected = "https://www.linkedin.com/edu/school?id=18973"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinProfile(unittest.TestCase):

    def setUp(self):
        self.service = BingRequestMaker("arianna huffington","linkedin_profile", extra_keywords="President and Editor-in-Chief at The Huffington Post Media Group")

    def test_linkedin_profile(self):
        expected = "https://www.linkedin.com/pub/arianna-huffington/40/158/aa7"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinExtended(unittest.TestCase):

    def setUp(self):
        self.service = BingRequestMaker("marissa mayer","linkedin_extended_network","Yahoo!, President & CEO")

    def test_linkedin_profile(self):
        #TODO find someone who passes this test
        expected = "https://www.linkedin.com/in/megwhitman"
        data = self.service.process()
        assert(expected in data)

def test_all():
    unittest.main()
    pass
