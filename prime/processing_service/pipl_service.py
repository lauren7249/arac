import json
import logging
import time
from random import shuffle
from service import Service
from pipl_request import PiplRequest

def wrapper(person, type):
    if type=="email":
        key = person.get("email")
    else:
        key = person.get("facebook")
    try:
        request = PiplRequest(key, type=type, level="social")
        data = request.process()
        person.update(data)
        return person
    except Exception, e:
        print __name__ + ": " + str(e)
        return person
        
def wrapper_email(person):
    return wrapper(person, type="email")

def wrapper_facebook(person):
    return wrapper(person, type="facebook")

class PiplService(Service):
    """
    Input:
            {"data":[{email, other info}]} 
    Output:
            {"data":[{email, pip info, other info}]} 
    """

    def __init__(self, data, *args, **kwargs):
        super(PiplService, self).__init__(data, *args, **kwargs)
        self.pool_size = 10
        self.wrapper = wrapper_email

class PiplFacebookService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts, images, and Linkedin IDs via PIPL
    """

    def __init__(self, data, *args, **kwargs):
        super(PiplFacebookService, self).__init__(data, *args, **kwargs)
        self.pool_size = 10
        self.wrapper = wrapper_facebook