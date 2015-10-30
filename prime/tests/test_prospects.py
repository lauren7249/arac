from flask import Flask
import urllib2
from flask.ext.sqlalchemy import SQLAlchemy
import unittest
from flask.ext.testing import TestCase, LiveServerTestCase

from prime.prospects.agent_model import Agent
from prime import create_app, db
from config import config


class MyTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        db.app = self.app
        db.init_app(self.app)
        db.create_all()

    def test_create_agent(self):
        agent = Agent(email="jamesjohnson11@gmail.com")
        db.session.add(agent)
        db.session.commit()
        assert agent in db.session

    def tearDown(self):
        db.session.remove()
        db.drop_all()

