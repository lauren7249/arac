import os
import datetime
import logging

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
from prime.users.models import User
from prime.customers.models import Customer

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

    user_id = db.Column(Integer, ForeignKey("users.user_id"), index=True)
    user = relationship('User', foreign_keys='ManagerProfile.user_id',
            backref='manager_profile')

    users = db.relationship(User, secondary=_manager_users,
            backref=db.backref('users'), lazy='dynamic')

    created = db.Column(Date)
    json = db.Column(JSON, default={})


    def get_id(self):
        return unicode(self.manager_id)

    def __str__(self):
        return 'Manager: {} {} ({})'.format(self.user.first_name,
                self.user.last_name, self.user.user_id)

    def __repr__(self):
        return 'Manager: {} {} ({})'.format(self.user.first_name,
                self.user.last_name, self.user.user_id)

