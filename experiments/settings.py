DB_CONNECTION = {
    "drivername": "postgresql",
    "kwargs": dict(
	username='arachnid', 
	password='gradiusdevlin', 
	host='arachnid.c5vjkeilta4u.us-east-1.rds.amazonaws.com',
	port=5432,
	database='arachnid'
    )
}

PHANTOMJS_PATH	= '~/phantomjs-1.9.7-linux-x86_64/bin/phantomjs' 

REDIS = {
    'host': 'redis.edpv6s.0001.use1.cache.amazonaws.com',
    'port': 6379
}

PROJECT_ROOT = '/home/ubuntu/arachnid/arachnid/experiments'
