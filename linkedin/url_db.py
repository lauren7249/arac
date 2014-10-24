import boto

class UrlDB(object):
    FINISHED_URL_SET     = 'finished_urls'
    FAILURE_KEY_TEMPLATE = 'server-failure-{}'
    FAILURE_LIMIT        = 10

    def __init__(self, redis):
        self.redis = redis

        # get a unique id through boto
        self.server_id = boto.utils.get_instance_metadata()['local-hostname']
        self.failure_key = FALURE_KEY_TEMPLATE.format(self.server_id)

    def is_url_finished(self, url):
        return self.redis.sismember(self.FINISHED_URL_SET, url)

    def mark_url_finished(self, url):
        return self.redis.sadd(self.FINISHED_URL_SET, url)

    def is_server_healthy(self):
        try:
            times = int(self.redis.get(failure_key))
            if times > self.FAILURE_LIMIT:
                return False
        except ValueError:
            return True

    def mark_failure(self):
        self.redis.incr(self.failure_key)

