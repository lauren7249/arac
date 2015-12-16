import os
import urlparse
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDIS_URL','http://localhost:6379')
conn = Redis()

with Connection(conn):
    worker = Worker(map(Queue, listen))
    worker.work()
