import argparse
import code
import os

from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from sqlalchemy.engine.url import URL

from prime import db

class Prospect(db.Model):
    __tablename__ = 'prospect'

    id = db.Column(Integer, primary_key=True)

    url = db.Column(String(1024))
    name = db.Column(String(1024))
    linkedin_id = db.Column(String(1024))

    location = db.Column(Integer, ForeignKey("location.id"))
    location_raw = db.Column(String)

    industry = db.Column(Integer, ForeignKey("industry.id"))
    industry_raw = db.Column(String(1024))

    s3_key = db.Column(String(1024))
    complete = db.Column(Boolean)
    updated = db.Column(Date)
    connections = db.Column(Integer)
    people_raw = db.Column(Text)

    @classmethod
    def linkedin_exists(cls, session, linkedin_id):
        (ret, ) = session.query(exists().where(
            Prospect.linkedin_id==linkedin_id
        ))
        return ret[0]

    @classmethod
    def s3_exists(cls, session, s3_key):
        (ret, ) = session.query(exists().where(
            Prospect.s3_key==s3_key
        ))
        return ret[0]

    def __repr__(self):
        return '<Prospect id={0} name={1} url={2}>'.format(
                self.id,
                self.name,
                self.url
                )


class Location(db.Model):
    __tablename__ = "location"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<Location id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Industry(db.Model):
    __tablename__ = "industry"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<Industry id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<Company id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(Integer, primary_key=True)
    company = db.Column(Integer, ForeignKey("company.id"))
    company_raw = db.Column(String(1024))
    location = db.Column(String(1024))

    user = db.Column(Integer, ForeignKey("prospect.id"))
    title = db.Column(String(1024))
    start_date = db.Column(Date)
    end_date = db.Column(Date)

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                self.company_raw,
                self.user.name
                )

class School(db.Model):
    __tablename__ = "school"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(1024))

    def __repr__(self):
        return '<School id={0} name={1}>'.format(
                self.id,
                self.name
                )


class Education(db.Model):
    __tablename__ = "prospect_school"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    school = db.Column(Integer, ForeignKey("school.id"))
    degree = db.Column(String(200))
    school_raw = db.Column(String(1024))
    user = db.Column(Integer, ForeignKey("prospect.id"))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    body_tsv = db.Column(TSVECTOR)

    def __repr__(self):
        return '<Education id={0} name={1} user={2}>'.format(
                self.id,
                self.school_raw,
                self.user.name
                )

