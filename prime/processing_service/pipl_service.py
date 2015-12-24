import json
import logging
import time
import multiprocessing
from random import shuffle
from service import Service
from pipl_request import PiplRequest

def wrapper(person):
    email = person.keys()[0]
    info = person.values()[0]
    request = PiplRequest(email, type="email", level="social")
    data = request.process()
    data.update(info)
    return {email:data}

class PiplService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts, images, and Linkedin IDs via PIPL
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(PiplService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.wrapper = wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
