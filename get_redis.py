import os
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
