from time import sleep
import os
import urlparse
import pprint
import argparse

from redis import Redis

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError('REDIS_URL must be defined to run the redis scraper')

def get_redis():
    urlparse.uses_netloc.append('redis')
    redis_url_parsed = urlparse.urlparse(redis_url)
    redis = Redis(
        host=redis_url_parsed.hostname,
        port=redis_url_parsed.port,
        db=0,
        password=redis_url_parsed.password
    )

    return redis

class RedisQueue(object):
    def __init__(self, key, instance_id=None):
        self.redis = get_redis()

        self.fail_set      = '{}-fail-set'.format(key)
        self.success_set   = '{}-success-set'.format(key)
        self.pending_set   = '{}-pending-set'.format(key)
        self.working_set   = '{}-working-set'.format(key)

        self.work_prefix = '{}-work'.format(key)
        self.work_key = instance_id

    def pop(self, block = True, timeout=1):
        return self.redis.spop(self.working_set)

    def pop_block(self, wait=1, tries = None):
        item = self.redis.spop(self.working_set)
        i = 0
        while True:
            if item:
                break

            sleep(wait)

            i += 1
            if tries and i > tries:
                break

            item = self.redis.spop(self.working_set)

        if item is not None:
            self.redis.sadd(self.working_set, item)

        return item

    def fail(self, value):
        # push to failure queue
        self.redis.smove(self.working_set, self.fail_set, value)
        if self.work_key:
            self.redis.hincr(self.work_prefix, self.work_key)

    def succeed(self, value):
        # push to success queue
        self.redis.smove(self.working_set, self.success_set, value)

    def seen(self, value, filter_failed=True):
        has_seen = self.redis.sismember(self.pending_set, value) or \
                   self.redis.sismember(self.success_set, value) or \
                   self.redis.sismember(self.working_set, value)
        if filter_failed:
            has_seen |= self.redis.sismember(self.fail_set, value)

        return has_seen

    def push(self, value, filter_seen=True, filter_failed=True):
        # check if the value is in our seen set, if it is
        # let it in
        filtered = False
        if filter_seen:
            filtered = self.seen(value, filter_failed=filter_failed)

        # push on the queue if we are not filtered
        if not filtered:
            self.redis.sadd(self.working_set, value)

    def unfail_all(self):
        failed = self.redis.smembers(self.fail_set)
        for f in failed:
            self.push(f, filter_failed=False)

        # delete the rest of the failures
        self.redis.delete(self.fail_set)

    def get_stats(self):
        # get all workers
        workers = self.redis.hgetall(self.work_prefix)

        return {
            'working': self.redis.scard(self.working_set),
            'pending': self.redis.scard(self.pending_set),
            'fail':    self.redis.scard(self.fail_set),
            'success': self.redis.scard(self.working_set),
            'failures': workers
        }

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('key')
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--unfail-all', action='store_true')

    args = parser.parse_args()

    q = RedisQueue(args.key)

    if args.stats:
        pprint.pprint(q.get_stats())
    if args.unfail_all:
        q.unfail_all()

if __name__ == '__main__':
    main()
