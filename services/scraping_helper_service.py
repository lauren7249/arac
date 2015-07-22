import web
import random
import getpass
import argparse
import datetime
import time

import tinys3, os, boto
from boto.s3.key import Key
from prime.utils import *

web.config.debug = False
urls = (
    '/select', 'select'
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

class select:
    def GET(self):
        return r.srandmember("urls")

if __name__ == "__main__":
    app.run()

