import redis
import re
import requests
import boto
import os 

redis_host='169.55.28.212'
redis_port=6379
new_redis_host='pub-redis-16531.dal-05.1.sl.garantiadata.com'
new_redis_dbname='65497c70-b709-4c85-acd5-97aa346ddf8d'
new_redis_port=16531
user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
headers ={'User-Agent':user_agent, 'Accept-Language': 'en-US,en;q=0.8', "Content-Language":"en"}
good_proxies ="good_proxies"
bad_proxies="bad_proxies"
in_use_proxies="in_use_proxies"
requests_session = requests.Session()
profile_re = re.compile('(^https?://www.linkedin.com/pub/((?!dir).)*/.*/.*)|(^https?://www.linkedin.com/in/.*)')
school_re = re.compile('^https://www.linkedin.com/edu/*')

def get_redis():
	pool = redis.ConnectionPool(host=new_redis_host, port=new_redis_port, password='yy8TrUZZgNLd8nEP')
	r = redis.Redis(connection_pool=pool)
	return r

r = get_redis() 

def get_bucket(bucket_name='chrome-ext-uploads'):
    s3conn = boto.connect_s3(os.getenv("AWS_ACCESS_KEY_ID_PVLL"), os.getenv("AWS_SECRET_ACCESS_KEY_PVLL"))
    return s3conn.get_bucket(bucket_name)