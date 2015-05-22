import redis

host='52.28.83.139'

def get_redis():
	pool = redis.ConnectionPool(host=host, port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	return r

r = get_redis() 