from time import sleep

class RedisQueue(object):
    def __init__(self, redis, key):
        self.redis = redis

        self.fail_set      = '{}-fail-set'.format(key)
        self.success_set   = '{}-success-set'.format(key)
        self.pending_set   = '{}-pending-set'.format(key)
        self.working_set   = '{}-working-set'.format(key)

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

    def succeed(self, value):
        # push to success queue
        self.redis.smove(self.working_set, self.success_set, value)

    def seen(self, value):
        return self.redis.sismember(self.pending_set, value) or \
               self.redis.sismember(self.fail_set, value)    or \
               self.redis.sismember(self.success_set, value) or \
               self.redis.sismember(self.working_set, value)

    def push(self, value, filter_seen=True):
        # check if the value is in our seen set, if it is
        # let it in
        filtered = False
        if filter_seen:
            filtered = self.seen(value)

        # push on the queue if we are not filtered
        if not filtered:
            self.redis.sadd(self.working_set, value)

