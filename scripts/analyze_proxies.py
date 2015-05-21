import pandas
import redis
import time 
import pickle
import os

host='proxiess.sqq1to.0001.euc1.cache.amazonaws.com'
pickle_output='results.pkl'

def get_redis():
	pool = redis.ConnectionPool(host=host, port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	return r

r = get_redis() 

try:
	f = open(pickle_output,"rb")
	df = pickle.load(f)
	f.close()
except:
	df = pandas.DataFrame()

while True:
	record = r.lpop("tested_proxies")
	if record is None:
		time.sleep(3)
		if r.llen("tested_proxies") == 0: break
		record = r.lpop("tested_proxies")
	d = eval(record)
	row = pandas.DataFrame.from_dict([d])
	df = pandas.concat([df,row])

f = open(pickle_output,'w')
pickle.dump(df,f)
df.to_csv("proxy_results.csv")
