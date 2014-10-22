class UrlDB(object):
    FINISHED_URL_SET = 'finished_urls'

    def __init__(self, redis):
	self.redis = redis
    
    def is_url_finished(self, url):
	return self.redis.sismember(self.FINISHED_URL_SET, url)

    def mark_url_finished(self, url):
	return self.redis.sadd(self.FINISHED_URL_SET, url)
    
