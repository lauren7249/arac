
# coding: utf-8

# In[ ]:

import sqlalchemy as sq
import sqlite3
import psycopg2
from datetime import date, datetime, timedelta
import random as rnd
import Queue as q
from threading import Thread
import time, signal
import timeit

# CONSTANTS
############
DB_USER = 'arachnid'
DB_PASS = 'devious8ob8'
RETRY_INTERVAL = timedelta(days=2)
CONSECUTIVE_FAIL_THRESHOLD = 3
MAX_DB_CONCURRENCY = 2
MAX_SCRAPER_CONCURRENCY = 100

# Generate some fake domains to work with
URL_COUNT = range(1,1000)
BIG_LIST_OF_URLS = map(lambda x: "https://{}.com".format(rnd.randint(1,10000000)),URL_COUNT)

print "###########################################"
print "#    SIMULATING DB_CONCURRENCY OF   {}     ".format(MAX_DB_CONCURRENCY)
print "#               SCRAPER_CONCURRENCY {}     ".format(MAX_SCRAPER_CONCURRENCY)
print "###########################################"


# In[ ]:


def db(schema='arachnid', host='babel.priv.advisorconnect.co', user=DB_USER, pwd=DB_PASS):
    
    """
     Connect to the database
     
     :param schema: Schema name (defaults to arachnid)
     :param host:   Databse server name (defaults to babel)
     :param user:   Username (defaults to DB_USER constant)
     :param pwd:    Database password (defaults to DB_PASS constant)
     
     :returns :Engine A SQLAlchemy DB Engine instance

    """
    engine = None
    
    try:
        connection_url = "postgresql+psycopg2://{user}:{pwd}@{host}/{schema}".format(user=user, pwd=pwd, 
                                                                                         host=host, schema=schema)

        ###########
        # Unless there are millions of rows, a local sqllite database
        # is a viable option, obliviating the need to involve 
        # postgres at all.
        #
        # http://sqlitebrowser.org/ can be used to manipulate the DB
        ###########
#       connection_url = "sqllite:///proxy.db"
    
        engine = sq.create_engine(connection_url, pool_size=5, isolation_level="READ_COMMITTED",
                                 strategy='threadlocal', echo=True, echo_pool=False)
    except Exception as e:
        print "Unable to connect to database, error: {}", str(e)
        raise
    finally:
        return engine
    


# In[ ]:

def get_list_of_urls():
    """
    Stubbed implementation.  Real one would retrieve from Redis
    """
    return BIG_LIST_OF_URLS


# In[ ]:

def get_proxy_via_proc(domain = "https://google.com", last_accepted_thresh = datetime.now(), 
                  last_rejected_thresh = datetime.now(), retry_interval = RETRY_INTERVAL, 
                  consequtive_fail_threshold = CONSECUTIVE_FAIL_THRESHOLD):

    """
    Retrieve a proxy instance given a domain
    WHERE 
    proxy NOT in_use AND consecutive_timeouts < CONSEQUTIVE_FAIL_THRESHOLD
      NOT (last_rejected >= last_rejected_thresh) || (last_accepted >= last_accepted_thresh)
    AND
          (last_timeout < retry_threshold) || (last_success > last_timeout)
          
    :param :domain The domain name we're requesting a proxy for
    :param :last_accepted_thresh The last accepted time threshold
    :param :last_rejected_thresh The last rejected time threshold
    :param :retry_interval Time interval in which we'll retry a previously failed proxy
    :param :consequtive_fail_threshold The number of consequtive failures after which we will no longer
              consider a proxy, regardless of the thresholds requested.
              
    :returns :proxy a Proxy instance or None
          
    """
    retry = datetime.now() - RETRY_INTERVAL
    
    with db() as d:  # This syntax safely returns the connection to the pool upon completion or failure
        
        cursor = d.raw_connection().cursor()  # Grab a psycopg2 cursor, sqlalchemy doesn't do stored procs
        
        # Call the get_proxy() proc with a tuple of parameters passed in and then fetch the result
        cursor.callproc('get_proxy',(domain,last_rejected_thresh,last_accepted_thresh))
        proxy = cursor.fetchone()
        
        return proxy
           


# In[ ]:

def get_proxy_max_optimization():
    """
    While this will be the highest performing option
    by removing the database as bottleneck, it is
    left to the programmer to decide on cost/benefit.
    
    In this scenario, daatabase access would be
    avoided where possible and would roughly entail
    
    1 - Retrieve the universe of possibly valid proxies
    2 - Place this list into a synchronized Collection or Dataframe
    3 - Check proxies in and out from this in memory struct
    4 - Batch updates to the database proxy_event tables
    5 - At end of run update the last success/fail/timeout values

    """


# In[ ]:

def get_proxy_via_reqular_queries(domain = "https://google.com", last_accepted_thresh = datetime.now(), 
                  last_rejected_thresh = datetime.now(), retry_interval = RETRY_INTERVAL, 
                  consequtive_fail_threshold = CONSECUTIVE_FAIL_THRESHOLD):
    """
    This stubbed method would work using the 'old' way - just regular sqlalchemy code
    """
    
    # Simulate query response time
    time.sleep(rnd.randint(0,2))
    
    return domain

def scraper(url, proxy):
    """
    Stub implementation of a scraper
    
    :param :url   The url to scrape
    :param :proxy The proxy to use 
    """
    # Simulate scraper response time
    time.sleep(rnd.randint(10,60))
    return "Scraped: {} using: {}".format(url, proxy)
    


# In[ ]:

def scraper_dispatch():
    """
    This worker dispatches to the real scraper
    method.  Upon completion, it notifies the
    task queue that it's done.  This implementation
    assumes that exceptions will be gracefully
    handled in the scraper method but we add
    a finally just in case -- the threads will
    live forever if not properly closed and 
    in some cases will persist even after 
    ctrl-c'ing or otherwise killing the main
    python thread.
    """
    while True:
        try:
            url, proxy = scrapersQueue.get()
            print scraper(url, proxy)
        finally:
            scrapersQueue.task_done()
            
            


# In[ ]:

def get_proxy_dispatch():
    """
    This worker dispatches to the real proxy
    query method.  Upon completion, it notifies the
    task queue that it's done.  This implementation
    assumes that exceptions will be gracefully
    handled in the proxy method but we add
    a finally just in case -- the threads will
    live forever if not properly closed and 
    in some cases will persist even after 
    ctrl-c'ing or otherwise killing the main
    python thread.
    
    Also, given the contention for limited
    resources, there are likely a dramatically
    mismatched proxy to target ratio so returning
    an open query slot is even more important.
    """
    while True:
        try:
            target = proxiesQueue.get()
            proxy = get_proxy_via_reqular_queries(domain=target)
            scrapersQueue.put((target, proxy))
        finally:
            proxiesQueue.task_done()


# In[ ]:

# Stand up the dispatch queues
proxiesQueue = q.Queue()
scrapersQueue = q.Queue()

"""
The following sytax is the idiomatic,
if odd, Pythonic way to dispatch threads
n at a time.

Left to the developer, signals are not 
captured (like ctrl-c) as it will be
caught on a random thread.

The signal library provides a way to
intercept this and pass up to the main
thread for handlig appropriately.

In lieu of, kill -9 will be required
"""
for i in range(MAX_DB_CONCURRENCY):
    t = Thread(target=get_proxy_dispatch)
    t.daemon = True
    t.start()
    
for target in get_list_of_urls():
    proxiesQueue.put(target)
    
for x in range(MAX_SCRAPER_CONCURRENCY):
    t = Thread(target=scraper_dispatch)
    t.daemon = True
    t.start()


# In[ ]:

# Block until complete
proxiesQueue.join() 
scrapersQueue.join() 



# In[ ]:



