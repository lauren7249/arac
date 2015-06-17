import redis

redis_host='169.55.28.212'
user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
headers ={'User-Agent':user_agent, 'Accept-Language': 'en-US,en;q=0.8', "Content-Language":"en"}
good_proxies ="good_proxies"
bad_proxies="bad_proxies"
in_use_proxies="in_use_proxies"

def get_redis():
	pool = redis.ConnectionPool(host=redis_host, port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	return r

r = get_redis() 

