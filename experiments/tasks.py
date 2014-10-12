from rq import Queue, Worker
from queues import redis_conn

from linkedin import process_next_request_task

def main():
    q = Queue('linkedin', connection=redis_conn)
    w = Worker(q, connection=redis_conn)
    w.work()

if __name__ == '__main__':
    main()
