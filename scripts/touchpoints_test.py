import pandas
import us
from prime.utils import googling, r
import multiprocessing

tp = pandas.read_csv("~/advisorCONNECT 6-10-15 Test Input.csv")
tp["zip"] = tp["Zip Code"].apply(lambda z: int(z.split("-")[0]))
#3500
tp.drop_duplicates(subset=["ID Number","zip"], inplace=True)
#2215
zips = pandas.read_csv("~/zipcode.csv")
zips.rename(columns={"latitude":"tp_lat","longitude":"tp_lng"}, inplace=True)
zips = zips[["zip","tp_lat","tp_lng"]]


tp =tp.merge(zips, how="inner", on=["zip"])
#2161

def process(row):
    if str(row["Middle Name"]) == "nan": terms = row["First Name"] + " " + row["Last Name"] + " " + us.states.lookup(row["State"]).name
    else: terms = row["First Name"] + " " + row["Middle Name"] + " " + row["Last Name"] + " " + us.states.lookup(row["State"]).name
    u = googling.search_linkedin_profile(terms)
    if len(u)==0 or u is None: 
    	print terms
    	return
    id = row["ID Number"]
    if r.hexists("touchpoints",id): u.update(eval(r.hget("touchpoints",id)))
    r.hset("touchpoints",id,u)

#pool = multiprocessing.Pool(10)
for index, row in tp.iterrows():
	process(row)
	#pool.apply_async(process, (row,))

pool.close()
pool.join()
