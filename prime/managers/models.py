import os
import datetime
import logging
import re
from flask import current_app
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from sqlalchemy import CheckConstraint
import sqlalchemy.event
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date, \
        Text, Enum, Float
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
from prime.customers.models import Customer
from prime.users.models import User

logger = logging.getLogger(__name__)

_manager_users = db.Table('manager_users',
                             db.Column('user_id', postgresql.INTEGER, db.ForeignKey('users.user_id',
                                                                                        ondelete='CASCADE'),
                                       nullable=False, index=True),
                             db.Column('manager_id', postgresql.INTEGER, db.ForeignKey('managers.manager_id',
                                                                                     ondelete='CASCADE'),
                                       nullable=False, index=True))


class ManagerProfile(db.Model, UserMixin):

    __tablename__ = 'managers'

    manager_id = db.Column(postgresql.INTEGER, primary_key=True)

    user_id = db.Column(Integer, ForeignKey("users.user_id"), index=True, unique=True)
    user = relationship('User', foreign_keys='ManagerProfile.user_id',
            backref='manager_profile')

    users = db.relationship(User, secondary=_manager_users,
            backref=db.backref('users'), lazy='dynamic')

    name_suffix = db.Column(String(500))
    certifications = db.Column(String(500))
    address = db.Column(String(1000), nullable=False)
    phone = db.Column(String(30))
    created = db.Column(Date, default=datetime.datetime.today())
    job_title =  db.Column(String(1500))
    
    @property 
    def invitations_sent(self):
        return int(self.users.count())

    @property 
    def prescreens_completed(self):
        return int(self.users.filter(User.hiring_screen_completed==True).count())

    @property 
    def candidates_hired(self):
        return int(self.users.filter(User.p200_started==True).count())

    @property 
    def p200s_completed(self):
        return int(self.users.filter(User.p200_submitted_to_manager==True).count())

    @property 
    def title(self):
        title = self.user.first_name + " " + self.user.last_name
        if self.name_suffix:
            title += ', ' + self.name_suffix
        if self.certifications:
            title += ', ' + self.certifications
        if self.job_title:
            title += ", " + self.job_title
        return title

    @property 
    def address_1(self):
        return self.address.split("\n")[0]

    @property 
    def address_2(self):
        return self.address.split("\n")[-1]

    @property 
    def html_signature(self):
        signature = "<p>" + self.title + "</p>"
        if self.address:
            signature += '<p>' + self.address.replace("\\n","</p><p>") + "</p>"
        if self.phone:
            signature += '<p>' + self.phone + "</p>"
        if self.user.email:
            signature += '<p>' + self.user.email + "</p>"
        return signature

    def get_id(self):
        return unicode(self.manager_id)

    def __str__(self):
        return 'Manager: {} {} ({})'.format(self.user.first_name,
                self.user.last_name, self.user.user_id)

    def __repr__(self):
        return 'Manager: {} {} ({})'.format(self.user.first_name,
                self.user.last_name, self.user.user_id)

    @property
    def image(self):
        if self.main_profile_image:
            return self.main_profile_image
        return "/static/img/shadow-avatar.png"