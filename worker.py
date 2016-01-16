import os
from redis import Redis, ConnectionError
from rq import Worker, Queue, Connection
from retrying import retry
from prime.processing_service.constants import REDIS_URL

listen = ['high', 'default', 'low']

def retry_if_connection_error(ex):
    """
    Return True if we should retry, else return False
    :param ex: Exception
    :return: Boolean
    """
    return isinstance(ex, ConnectionError)


@retry(retry_on_exception=retry_if_connection_error, stop_max_attempt_number=10, wait_fixed=5000)
def do_work():
    """
    Activate the Redis worker, retrying up to 10 times at 5 second intervals
    should redis not be immediately available
    """
    try:
        conn = Redis.from_url(url=REDIS_URL, db=0)

        with Connection(conn):
            worker = Worker(map(Queue, listen))
            worker.work()
    except ConnectionError:
        print('Connection Error, will attempt a retry up to 10 times.')
        raise


if __name__ == '__main__':
    do_work()
