import os
import urlparse
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = 'redis://consumer.btwauj.0001.use1.cache.amazonaws.com:6379'
if not redis_url:
    raise RuntimeError('Set up Redis To Go first.')

urlparse.uses_netloc.append('redis')
url = urlparse.urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

with Connection(conn):
    worker = Worker(map(Queue, listen))
    worker.work()
