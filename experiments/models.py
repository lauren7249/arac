import argparse
import code

from sqlalchemy import create_engine, Column, Integer, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import settings

Base = declarative_base()

class ScrapeRequest(Base):
    __tablename__ = 'scrape_requests'

    id	    = Column(Integer, primary_key=True)
    done    = Column(Boolean, default=False)
    url	    = Column(String)
    html    = Column(String)

    @classmethod
    def get_unfinished_request(cls, session):
	return session.query(ScrapeRequest).filter(ScrapeRequest.done == False).first()
    
    def __repr__(self):
	return '<ScrapeRequest id={0} done={1} url={2}>'.format(
	    self.id,
	    self.done,
	    self.url
	)

engine = create_engine(settings.DB_CONNECTION)
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
