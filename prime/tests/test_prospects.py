import json
import urllib2
import unittest
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.testing import TestCase, LiveServerTestCase

from prime.processing_service.cloudsponge_service import CloudSpongeService
from prime.processing_service.clearbit_service import ClearbitService
from prime.processing_service.pipl_service import PiplService
from prime.processing_service.linkedin_service import LinkedinService
from prime.processing_service.glassdoor_service import GlassdoorService
from prime.processing_service.indeed_service import IndeedService

from prime import create_app, db
from config import config

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
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        emails = {"jamesjohnson11@gmail.com":{}}
        self.service = PiplService(email, linkedin_url, emails)

    def test_pipl(self):
        expected = [{'jamesjohnson11@gmail.com': {'linkedin_urls': u'http://www.linkedin.com/pub/james-johnson/a/431/7a0',
            'social_accounts': [u'http://www.linkedin.com/pub/james-johnson/a/431/7a0',
                u'https://plus.google.com/106226923266702208073/about']}}]
        data = self.service.process()
        self.assertEqual(data, expected)


class TestClearbitService(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        emails = [{"alex@alexmaccaw.com":{}}]
        self.service = ClearbitService(email, linkedin_url, emails)

    def test_clearbit(self):
        expected = [{'alex@alexmaccaw.com': {'linkedin_urls': u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
            'social_accounts': [u'https://twitter.com/maccaw',
                u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
                u'https://facebook.com/amaccaw',
                u'https://angel.co/maccaw',
                u'https://github.com/maccman',
                u'https://aboutme.com/maccaw',
                u'https://gravatar.com/maccman']}}]
        data = self.service.process()
        self.assertEqual(data, expected)


class TestClearbitRequest(unittest.TestCase):

    def setUp(self):
        email = "jamesjohnson11@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/jamesjohnsona"
        emails = [{"alex@alexmaccaw.com":{}}]
        self.service = ClearbitService(email, linkedin_url, emails)

    def test_clearbit(self):
        expected = [{'alex@alexmaccaw.com': {'linkedin_urls': u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
            'social_accounts': [u'https://twitter.com/maccaw',
                u'https://www.linkedin.com/pub/alex-maccaw/78/929/ab5',
                u'https://facebook.com/amaccaw',
                u'https://angel.co/maccaw',
                u'https://github.com/maccman',
                u'https://aboutme.com/maccaw',
                u'https://gravatar.com/maccman']}}]
        data = self.service.process()
        self.assertEqual(data, expected)


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

if __name__ == '__main__':
    unittest.main()
