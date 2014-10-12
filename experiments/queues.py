from rq import Queue
from redis import Redis
from settings import REDIS
redis_conn = Redis(**REDIS)
queue = Queue(connection=redis_conn)


