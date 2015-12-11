import json
import logging
import time
import multiprocessing
from random import shuffle
from service import Service
from pipl_request import PiplRequest

def unwrap_process(person):
    request = PiplRequest(person)
    return request.process()

class PiplService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts, images, and Linkedin IDs via PIPL
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PiplService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def multiprocess(self, poolsize=5):
        #pipl limits you to 20 hits/second. if you go above a pool size of 5, this could be an issue.
        self.logger.info('Starting MultiProcess: %s', 'Pipl Service')
        items_array = [person for person, info in self.data.iteritems()]
        pool = multiprocessing.Pool(processes=poolsize)
        self.results = pool.map(unwrap_process, items_array)
        pool.close()
        pool.join()
        for i in xrange(0, len(items_array)):
            self.output.append({items_array[i]:self.results[i]})
        self.logger.info('Ending MultiProcess: %s', 'Pipl Service')
        return self.output

    def process(self):
        self.logger.info('Starting Process: %s', 'Pipl Service')
        for person, info in self.data.iteritems():
            request = PiplRequest(person, type="email", level="social")
            data = request.process()
            self.output.append({person:data})
        self.logger.info('Ending Process: %s', 'Pipl Service')
        return self.output

