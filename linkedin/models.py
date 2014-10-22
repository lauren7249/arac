from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class LinkedInScrape(Base):
    __tablename__ = 'linkedin_scrape'

    STATE_NEW     = 'new'
    STATE_WORKING = 'working'
    STATE_DONE    = 'done'

    STATES = [ STATE_NEW, STATE_WORKING, STATE_DONE ]

    id                  = Column(Integer, primary_key=True)
    url                 = Column(String)
    html                = Column(String)
    full_name           = Column(String)

    state               = Column(Enum(*STATES, default=STATE_NEW))
    date_created        = Column(DateTime, default=func.now())
    date_work_started   = Column(DateTime)
    date_completed      = Column(DateTime)

Session = sessionmaker()

def create(engine):
    Base.metadata.create_all(engine)

