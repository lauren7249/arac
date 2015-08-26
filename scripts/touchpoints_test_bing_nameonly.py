import pandas
import us
import datetime
from prime.utils import bing, r, geocode
from prime.prospects.get_prospect import *
from geoindex.geo_point import GeoPoint

tp = pandas.read_csv("~/advisorCONNECT 6-10-15 Test Input.csv")
tp["zip"] = tp["Zip Code"].apply(lambda z: int(z.split("-")[0]))
#3500
tp.drop_duplicates(subset=["First Name","Last Name", "Age", "zip"], inplace=True)
#2215
zips = pandas.read_csv("~/zipcode.csv")
zips.rename(columns={"latitude":"tp_lat","longitude":"tp_lng"}, inplace=True)
zips = zips[["zip","tp_lat","tp_lng"]]

tp =tp.merge(zips, how="inner", on=["zip"])
#2161


for index, row in tp.iterrows():
    #name = get_name(row)
    name = row["First Name"] + " " + row["Last Name"]
    urls = bing.search_linkedin_by_name(name, page_limit=10, limit=300)
    for url in urls:
        if r.sismember("urls",url): continue
        p = from_url(url)
        if p:
            if not p.updated or (datetime.datetime.now().date() - p.updated).days > 30:
                r.sadd("urls",url)
            # elif not p.age and (p.jobs or p.schools) : 
            #     print url

locations = {}
df = pandas.DataFrame()
for index, row in tp.iterrows():
    #name = get_name(row)
    name = row["First Name"] + " " + row["Last Name"]
    urls = bing.search_linkedin_by_name(name, page_limit=10, limit=300)
    has_real_match = False
    partial_matches = []
    for url in set(urls):
        newrow = row
        p = from_url(url)
        if not p: continue
        #if not p or not p.updated or (datetime.datetime.now().date() - p.updated).days > 30: continue
        age_matches = p.age and row.Age and abs(p.age - row.Age) <=5

        mapquest_coords = locations.get(p.location_raw) 
        if mapquest_coords is None:
            mapquest_coords = geocode.get_mapquest_coordinates(p.location_raw)
            locations[p.location_raw] = mapquest_coords if mapquest_coords else {}
        try:
            latlng = mapquest_coords.get("latlng")
            point1 = GeoPoint(latlng[0],latlng[1])
            point2 = GeoPoint(row.tp_lat, row.tp_lng)
            miles_apart = point2.distance_to(point1) 
        except:
            latlng = None
            miles_apart = None
        location_matches = miles_apart is not None and miles_apart < 75
        if not location_matches and not age_matches: continue
        newrow['li_url'] = url
        newrow['li_location'] = p.location_raw
        newrow['li_age'] = p.age
        newrow['matches_age'] = age_matches
        newrow['matches_location'] = location_matches
        newrow['miles_apart'] = miles_apart
        if latlng: 
            newrow['li_mapquest_lat'] = latlng[0]
            newrow['li_mapquest_lon'] = latlng[1]
        if mapquest_coords and mapquest_coords.get("latlng_result"):
            newrow['li_mapquest_result_name'] = mapquest_coords.get("latlng_result").get("name")
            newrow['li_mapquest_result_cc'] = mapquest_coords.get("latlng_result").get("cc")
        if location_matches and age_matches: 
            has_real_match = True
            newrow['matches_fully'] = True
            df = df.append(newrow, ignore_index=True)
        else:
            newrow['matches_partially'] = True
            partial_matches.append(newrow)
    if not has_real_match:
        if len(partial_matches):
            for newrow in partial_matches:
                df = df.append(newrow, ignore_index=True)
        else:
            df = df.append(row, ignore_index=True)

df.to_csv('/Users/lauren/Documents/data/touchpoints.output.csv', encoding='utf-8')
df.fillna(False, inplace=True)
matched_df = df[df.matches_fully==1.0]
matched_df.to_csv('/Users/lauren/Documents/data/matched.touchpoints.output.csv', encoding='utf-8')
#214
print len(set(matched_df["ID Number"].values))
#233
print len(set(matched_df["li_url"].values))
matched_df_partial = df[df.matches_partially==1.0]
#930
print len(set(matched_df_partial["ID Number"].values))
#1718
print len(set(df["ID Number"].values))
#1718
print len(set(tp["ID Number"].values))

#253
print len(set(tp[tp.Age < 40]["ID Number"].values))
#74
print len(set(matched_df[matched_df.Age < 40]["ID Number"].values))
