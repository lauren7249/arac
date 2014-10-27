import argparse
import code

from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

import settings

Base = declarative_base()

class Prospect(Base):
    __tablename__ = 'prospect'

    id = Column(Integer, primary_key=True)
    url = Column(String(120))
    name = Column(String(100))
    location = Column(Integer, ForeignKey("location.id"))
    industry = Column(Integer, ForeignKey("industry.id"))

    def __repr__(self):
        return '<Prospect id={0} name={1} url={2}>'.format(
                self.id,
                self.name,
                self.url
                )


class Location(Base):
    __tablename__ = "location"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    def __repr__(self):
        return '<Location id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Industry(Base):
    __tablename__ = "industry"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    def __repr__(self):
        return '<Industry id={0} name={1}>'.format(
                self.id,
                self.name
                )

class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    def __repr__(self):
        return '<Company id={0} name={1}>'.format(
                self.id,
                self.name
                )


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company.id"))
    user = Column(Integer, ForeignKey("prospect.id"))
    start_date = Column(Date)
    end_date = Column(Date)

    def __repr__(self):
        return '<Job id={0} name={1} user={2}>'.format(
                self.id,
                self.company.name
                self.user.name
                )


class School(Base):
    __tablename__ = "school"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    def __repr__(self):
        return '<School id={0} name={1}>'.format(
                self.id,
                self.name
                )


class Education(Base):
    __tablename__ = "school"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    company = Column(Integer, ForeignKey("school.id"))
    user = Column(Integer, ForeignKey("prospect.id"))

    def __repr__(self):
        return '<Education id={0} name={1} user={2}>'.format(
                self.id,
                self.company.name
                self.user.name
                )


engine_url = URL(
    settings.DB_CONNECTION['drivername'],
    **settings.DB_CONNECTION['kwargs']
)

engine = create_engine(engine_url)
Session = sessionmaker(bind=engine)

def create():
    Base.metadata.create_all(engine)

def shell():
    session = Session()
    code.InteractiveConsole(locals=locals()).interact()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--shell',  action='store_true')

    args = parser.parse_args()

    if args.create:
        create()
    if args.shell:
        shell()
