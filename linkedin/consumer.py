import logging
import json

from kinesis_consumer.consumer import Consumer

from . import models

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

        # try to get the result corresponding to this row
        return True


def add_url(url, session=None, commit=True, add_task=True):
    if session is None:
    session = Session()

    if not session.query(ScrapeRequest).filter(ScrapeRequest.url==url).count():
    logging.debug('Adding scrape request for {} to the queue'.format(url))
    new_request =  ScrapeRequest(
        url = url
    )
    session.add(new_request)
    session.commit()

    if add_task:
        process_next_request_task.delay(new_request.id)
 
