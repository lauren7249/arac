import json
import unittest
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.testing import TestCase, LiveServerTestCase

from prime.processing_service.cloudsponge_service import CloudSpongeService
from prime.processing_service.clearbit_service import ClearbitPersonService, ClearbitPhoneService
from prime.processing_service.pipl_service import PiplService
from prime.processing_service.linkedin_service import LinkedinService
from prime.processing_service.glassdoor_service import GlassdoorService
from prime.processing_service.indeed_service import IndeedService
from prime.processing_service.bing_service import BingService
from prime.processing_service.bloomberg_service import BloombergRequest, BloombergPhoneService
from prime.processing_service.phone_service import PhoneService
from prime.processing_service.mapquest_service import MapQuestRequest
from prime.processing_service.geocode_service import GeoCodingService
from prime.processing_service.gender_service import GenderService
from prime.processing_service.age_service import AgeService
from prime.processing_service.college_degree_service import CollegeDegreeService
from prime import create_app, db
from config import config

class TestCollegeDegreeService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = CollegeDegreeService(None, None, data)

    def test_college(self):
        data = self.service.process()
        self.assertEqual(data[0].get("college_grad"), True)
        self.assertEqual(data[1].get("college_grad"), True)

class TestAgeService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = AgeService(None, None, data)

    def test_age(self):
        data = self.service.process()
        self.assertEqual(data[0].get("age"), 27.5)
        self.assertEqual(data[1].get("age"), 25.5)

class TestGeoCodingService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = GeoCodingService(email, linkedin_url, data)

    def test_geocode(self):
        expected = (40.713054, -74.007228)
        data = self.service.process()
        latlng = data[1].get("location_coordinates").get("latlng")
        self.assertEqual(latlng, expected)

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

class TestCloudspongeService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        emails = [{"email":[{"address": "jamesjohnson11@gmail.com"}]},
                {"email":[{"address": "jamesjohnson11@gmail.com"}]}]
        self.service = CloudSpongeService(email, linkedin_url, emails)

    def test_pipl(self):
        expected = {'jamesjohnson11@gmail.com': {'companies': None, 'job_title': None}}
        data = self.service.process()
        self.assertEqual(data, expected)


class TestPiplService(unittest.TestCase):

    def setUp(self):
        emails = {"jamesjohnson11@gmail.com":{}}
        self.service = PiplService(None, None, emails)

    def test_pipl(self):
        data = self.service.process()
        self.assertEqual(data[0].get("jamesjohnson11@gmail.com").get("social_accounts"), [u'http://www.linkedin.com/pub/james-johnson/a/431/7a0',
                u'https://plus.google.com/106226923266702208073/about'])

class TestClearbitPersonService(unittest.TestCase):

    def setUp(self):
        emails = [{"alex@alexmaccaw.com":{}}]
        self.service = ClearbitPersonService(None, None, emails)

    def test_clearbit(self):
        data = self.service.process()
        self.assertEqual(data[0].get('alex@alexmaccaw.com').get("social_accounts"), [u'https://twitter.com/maccaw',
                u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
                u'https://facebook.com/amaccaw',
                u'https://angel.co/maccaw',
                u'https://github.com/maccman',
                u'https://aboutme.com/maccaw',
                u'https://gravatar.com/maccman'])

class TestClearbitPhoneService(unittest.TestCase):

    def setUp(self):
        data = [{}]
        data[0]["company_website"] = "www.boozallen.com"
        self.service = ClearbitPhoneService(None, None, data)

    def test_clearbit(self):
        expected_phone = '+1 703-902-5000'
        data = self.service.process()
        phone = data[0].get("phone_number")
        self.assertEqual(phone, expected_phone)


class TestBloombergRequest(unittest.TestCase):

    def setUp(self):
        name = "kpmg"
        self.service = BloombergRequest(name)

    def test_bloomberg(self):
        expected_phone = '212-758-9700'
        expected_website = 'http://www.kpmg.com/us'
        data = self.service.processNext()
        data = self.service.processNext()
        phone = data.get("phone")
        website = data.get("website")
        self.assertEqual(phone, expected_phone)
        self.assertEqual(website, expected_website)

class TestPhoneService(unittest.TestCase):

    def setUp(self):
        from fixtures.linkedin_fixture import expected
        self.data = expected

    def test_phone(self):
        self.service = PhoneService(None, None, self.data)
        expected = '(650) 573-3100'
        data = self.service.process(favor_mapquest=True)
        phone = data[2].get("phone_number")
        self.assertEqual(phone, expected)

    def test_phone2(self):
        self.service = PhoneService(None, None, self.data)
        expected = '+1 650-573-3100'
        data = self.service.process(favor_mapquest=True, favor_clearbit=True)
        phone = data[2].get("phone_number")
        self.assertEqual(phone, expected)

class TestBloombergPhoneService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = BloombergPhoneService(email, linkedin_url, data)

    def test_bloomberg(self):
        data = self.service.process()
        self.assertEqual(data[1].get("phone_number"), '800-507-9396')
        self.assertEqual(data[2].get("phone_number"), '650-573-3100')

class TestGenderService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = GenderService(email, linkedin_url, data)

    def test_gender(self):
        data = self.service.process()
        self.assertEqual(data[0].get("gender"), 'Female')
        self.assertEqual(data[1].get("gender"), 'Unknown')

class TestLinkedinService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        data = [{u'julia.mailander@gmail.com':
                {'linkedin_urls': u'http://www.linkedin.com/pub/julia-mailander/11/898/614',
                'social_accounts': [u'http://www.linkedin.com/pub/julia-mailander/11/898/614',\
                        u'https://plus.google.com/103608304178303305879/about']}
                }]
        self.service = LinkedinService(email, linkedin_url, data)

    def test_linkedin(self):
        expected = ['https://www.linkedin.com/pub/john-chen/1b/215/b97',
                               'https://www.linkedin.com/pub/jake-saper/0/834/536',
                               'https://www.linkedin.com/pub/brian-jacobs/0/a/7a6',
                               'https://www.linkedin.com/pub/jason-green/1/22b/409',
                               'https://www.linkedin.com/pub/joseph-floyd/2/8a4/55b',
                               'https://www.linkedin.com/pub/alison-wagonfeld/0/669/829',
                               'https://www.linkedin.com/pub/gordon-ritter/1/b95/a97',
                               'https://www.linkedin.com/pub/kate-berger/18/215/a01',
                               'https://www.linkedin.com/pub/everett-cox/3/9b6/9b8',
                               'https://www.linkedin.com/pub/santi-subotovsky/0/2b2/6b0']
        data = self.service.process()
        self.assertEqual(data[0].get("linkedin_data").get("urls"), expected)


class TestGlassdoorService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = GlassdoorService(email, linkedin_url, data)

    def test_glassdoor(self):
        #TODO find someone who passes this test
        expected = None
        data = self.service.process()
        salary = data[0].get("glassdoor_salary")
        self.assertEqual(salary, expected)

class TestIndeedService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        from fixtures.linkedin_fixture import expected
        data = expected
        self.service = IndeedService(email, linkedin_url, data)

    def test_indeed(self):
        #TODO find someone who passes this test
        expected = 79000
        data = self.service.process()
        salary = data[0].get("indeed_salary")
        self.assertEqual(salary, expected)

class BingServiceLinkedinCompany(unittest.TestCase):

    def setUp(self):
        name = "triplemint"
        self.service = BingService(name, "linkedin_company")

    def test_linkedin_company(self):
        expected = "https://www.linkedin.com/company/triple-mint"
        data = self.service.process()
        assert(expected in data)

class BingServiceBloombergCompany(unittest.TestCase):

    def test_bloomberg_company(self):
        self.service = BingService("farmivore", "bloomberg_company")
        expected = "http://www.bloomberg.com/research/stocks/private/snapshot.asp?privcapId=262829137"
        data = self.service.process()
        assert(expected in data)
        self.service = BingService("emergence capital partners", "bloomberg_company")
        expected = "http://www.bloomberg.com/research/stocks/private/snapshot.asp?privcapId=4474737"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinSchool(unittest.TestCase):

    def setUp(self):
        name = "marist college"
        self.service = BingService(name, "linkedin_school")

    def test_linkedin_school(self):
        expected = "https://www.linkedin.com/edu/school?id=18973"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinProfile(unittest.TestCase):

    def setUp(self):
        self.service = BingService("arianna huffington","linkedin_profile", extra_keywords="President and Editor-in-Chief at The Huffington Post Media Group")

    def test_linkedin_profile(self):
        expected = "https://www.linkedin.com/pub/arianna-huffington/40/158/aa7"
        data = self.service.process()
        assert(expected in data)

class BingServiceLinkedinExtended(unittest.TestCase):

    def setUp(self):
        self.service = BingService("marissa mayer","linkedin_extended_network","Yahoo!, President & CEO")

    def test_linkedin_profile(self):
        #TODO find someone who passes this test
        expected = "https://www.linkedin.com/in/megwhitman"
        data = self.service.process()
        assert(expected in data)

if __name__ == '__main__':
    unittest.main()