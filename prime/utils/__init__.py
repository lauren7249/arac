import redis

host='52.28.83.139'
ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
headers ={'User-Agent':ua, 'Accept-Language': 'en-US,en;q=0.8', "Content-Language":"en","Referer":"https://www.google.com/"}

def get_redis():
	pool = redis.ConnectionPool(host=host, port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	return r

r = get_redis() 