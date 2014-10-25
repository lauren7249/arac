class RedisQueue(object):
    def __init__(
            self, redis,
            pending_queue, working_queue,
            fail_queue, success_queue, seen_set):
        self.redis = redis
        self.pending_queue = pending_queue
        self.working_queue = working_queue
        self.fail_queue    = fail_queue
        self.success_queue = success_queue
        self.seen_set      = seen_set

    def __get_push(self, block=False):
        if block:
            return self.redis.brpoplpush
        else:
            return self.redis.rpoplpush

    def pop(self, block=True):
        return self.__get_push(block)(self.pending_queue, self.working_queue)

    def fail(self, value):
        # push to failure queue
        self.redis.rpush(self.fail_queue, value)
        self.redis.lrem(self.working_queue, 0, value)

    def succeed(self, value):
        # push to success queue
        self.redis.rpush(self.fail_queue, value)
        self.redis.lrem(self.working_queue, 0, value)

    def push(self, value, filter_seen=True):
        # check if the value is in our seen set, if it is
        # let it in
        filtered = False
        if filter_seen:
            filtered = self.redis.sismember(self.seen_set, value)

        # push on the queue if we are not filtered
        if not filtered:
            self.redis.rpush(self.pending_queue, value)
