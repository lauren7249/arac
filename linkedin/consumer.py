import logging
import json
import os

from sqlalchemy import create_engine

from kinesis_consumer.consumer import Consumer
from kinesis_consumer import models as kinesis_models

from .models import LinkedInScrape, Session
from .run_redis_scraper import process_request_job

class LinkedInConsumer(Consumer):
    def __init__(self, db_session, *args, **kwargs):
        self.db_session = db_session

        super(ArachnidConsumer, self).__init__(*args, **kwargs)

    def refresh_db_session(self):
        pass

    def process(self, row_json):
        '''we expect the row to be json data with
           related_urls: to the urls we plan on scheduling to process
           html:         the html string we have scraped
           full_name:    the full name of the linked in user
           url:          the url that this was scraped from'''

        self.refresh_db_session()

        row = json.loads(row_json)

        print row

        # try to get the result corresponding to this row
        return True

if __name__ == '__main__':
    db_url        = os.getenv('RESULTS_DB_URL')
    stream_db_url = os.getenv('STREAM_DB_URL')
    stream        = os.getenv('KINESIS_STREAM')
    shard_id      = os.getenv('KINESIS_SHARD')

    engine = create_engine(db_url)
    stream_engine = create_engine(stream_db_url)

    db_session         = Session(bind=engine)
    kinesis_db_session = kinesis_models.Session(bind=engine)

    consumer = LinkedInConsumer(db_session, stream, shard_id, kinesis_db_session)
    consumer.process()

