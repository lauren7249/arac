import os
import re
import string
import random
import logging

from flask import current_app
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from sqlalchemy import CheckConstraint
import sqlalchemy.event
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL

from prime import db

logger = logging.getLogger(__name__)

def slugify(s):
    alphanumeric = re.compile(r'[^a-zA-Z0-9]+')
    slug = alphanumeric.sub('-', s.lower()).strip('-')[:35]
    if len(slug) == 0:
        return random.choice(string.lowercase)
    return slug


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024), nullable=False)
    slug = db.Column(String(120))
    users = relationship('User', foreign_keys='User.customer_id')

    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Customer, self).save(*args, **kwargs)

    def __str__(self):
        return '{}'.format(self.name)


    @staticmethod
    def create_customer(name):
        slug = slugify(name)
        return Customer(name=name,slug=slug)
