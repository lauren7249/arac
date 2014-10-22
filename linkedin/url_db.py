class UrlDB(object):
    FINISHED_URL_SET = 'finished_urls'

    def __init__(self, redis):
	self.redis = redis
    
    def is_url_finished(self, url):
	return self.redis.sismember(url, self.FINISHED_URL_SET)

    def mark_url_finished(self, url):
	return self.redis.sadd(url, self.FINISHED_URL_SET)
    
