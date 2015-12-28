import json
import logging
import time
import multiprocessing
from random import shuffle
from service import Service
from pipl_request import PiplRequest

def wrapper(person, type):
    key = person.keys()[0]
    info = person.values()[0]
    request = PiplRequest(key, type=type, level="social")
    data = request.process()
    data.update(info)
    return {key:data}

def wrapper_email(person):
    return wrapper(person, type="email")

def wrapper_facebook(person):
    return wrapper(person, type="facebook")

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
        self.wrapper = wrapper_email
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

class PiplFacebookService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts, images, and Linkedin IDs via PIPL
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(PiplFacebookService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.wrapper = wrapper_facebook
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)