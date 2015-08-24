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

require_proxy=True
obs = 10000
tp =tp.merge(zips, how="inner", on=["zip"])
#2161

# for index, row in tp.iterrows():
#     id = row["ID Number"]
#     if str(row["Middle Name"]) == "nan":
#         name = row["First Name"] + " " + row["Last Name"]
#     else:
#         name = row["First Name"] + " " + row["Middle Name"] + " " + row["Last Name"]
#     terms = name  + " " + us.states.lookup(row["State"]).name   
#     u = googling.search_linkedin_profile(terms, name, require_proxy=require_proxy)

def process(row):
    id = row["ID Number"]
    #if r.hexists("touchpoints",id): return
    if str(row["Middle Name"]) == "nan": 
        name = row["First Name"] + " " + row["Last Name"]
    else: 
        name = row["First Name"] + " " + row["Middle Name"] + " " + row["Last Name"]
    terms = name  + " " + us.states.lookup(row["State"]).name   
    u = googling.search_linkedin_profile(terms, name, require_proxy=require_proxy)
    print u
    # if len(u)==0 or u is None: 
    # 	print "Nothing!"
    # 	return
    #if r.hexists("touchpoints",id): u.update(eval(r.hget("touchpoints",id)))
    #r.hset("touchpoints",id,u)

#pool = multiprocessing.Pool(10)
for index, row in tp.iterrows():
    #if index > obs: break
    process(row)
    #pool.apply_async(process, (row,))

pool.close()
pool.join()
