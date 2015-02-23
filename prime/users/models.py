import os
import logging

from flask import current_app
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from sqlalchemy import CheckConstraint
import sqlalchemy.event
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date, \
        Text, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import SchemaType, TypeDecorator, Enum

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL

from prime import db, login_manager
from prime.prospects.models import Prospect

logger = logging.getLogger(__name__)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(postgresql.INTEGER, primary_key=True)

    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)
    email = db.Column(String(100), nullable=False, unique=True)
    _password_hash = db.Column('password_hash', String(100), nullable=False)
    is_admin = db.Column(postgresql.BOOLEAN, nullable=False, server_default="FALSE")
    tour_completed = db.Column(postgresql.BOOLEAN, nullable=False, server_default="FALSE")
    customer_id = db.Column(Integer, ForeignKey("customers.id"))
    customer = relationship('Customer', foreign_keys='User.customer_id')
    linkedin_id = db.Column(String(1024))
    linkedin_url = db.Column(String(1024))
    json = db.Column(JSON)

    def __init__(self, first_name, last_name, email, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.first_name = first_name.title()
        self.last_name = last_name.title()
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.user_id)

    def generate_reset_token(self):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 3600)
        return s.dumps({'reset': self.user_id})

    @staticmethod
    def reset_password(token, new_password):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 3600)
        try:
            data = s.loads(token)
            u = User.query.get(data.get('reset'))
        except:
            return None
        if u is None:
            return None
        u.password = new_password
        db.session.add(u)
        return u

    @property
    def name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __str__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ClientType(db.Model):
    __tablename__ = "client_type"

    client_type_id = db.Column(postgresql.INTEGER, primary_key=True)
    processed = db.Column(Boolean, default=False)
    good = db.Column(Boolean, default=False)
    status = db.Column(String(100))



class Client(db.Model):
    __tablename__ = "clients"

    client_id = db.Column(postgresql.INTEGER, primary_key=True)

    user_id = db.Column(Integer, ForeignKey("users.user_id"), index=True)
    user = relationship('User', foreign_keys='Client.user_id')

    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='Client.prospect_id')

    type_id = db.Column(Integer, ForeignKey("client_type.client_type_id"), index=True)
    type = relationship("ClientType", foreign_keys='Client.type_id')



    def __str__(self):
        return '{}:{})'.format(self.user.first_name, self.prospect.first_name)
