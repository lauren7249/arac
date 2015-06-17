import pandas
from geopy.distance import vincenty

#campaign contributions
donors = pandas.read_csv("us.gov.fec.summary.2012", low_memory=False)

#remove institutional donors
donors.dropna(subset=["contributor_gender"], inplace=True)
donors = donors[donors.contributor_type == "I"]

#match columns
match_cols = ["contributor_name", "contributor_city", "contributor_state","contributor_zipcode","contributor_occupation","contributor_employer"]

#other keep columns
other_cols = ["amount","contributor_ext_id", "recipient_party","recipient_state","contributor_gender"]

#look at non-null
#donors[pandas.notnull(donors.contributor_employer)].contributor_employer

keep_cols = match_cols + other_cols

donors = donors[keep_cols]
donors.dropna(subset=["contributor_name"], inplace=True)
donors.dropna(subset=["contributor_employer"], inplace=True)
donors.dropna(subset=["contributor_zipcode"], inplace=True)
donors.dropna(subset=["contributor_occupation"], inplace=True)
donors.dropna(subset=["amount"], inplace=True)

#only people with first and last names
donors = donors[donors.contributor_name.str.find(", ") > -1]

#parse name
donors["last_name"] = donors.contributor_name.apply(lambda f: f.split(",")[0].upper())
donors["first_name"] = donors.contributor_name.apply(lambda f: f.split(",")[1])
donors["first_name"] = donors.first_name.apply(lambda f: f.strip().split(" ")[0].upper())

donors["employer"] = donors.contributor_employer.apply(lambda f: f.split("/")[0])
donors.employer = donors.employer.apply(lambda f: f.upper())
donors.contributor_occupation = donors.contributor_occupation.apply(lambda f: f.upper())

#from donors.employer.value_counts()
non_employers = ["RETIRED", "SELF-EMPLOYED", "RETIRED", "SELF", "NONE", "SELF-EMPLOYED", "SELF EMPLOYED", "INFORMATION REQUESTED", "INFORMATION REQUESTED PER BEST EFFORTS", "HOMEMAKER", "SELF", "INFORMATION REQUESTED", "NOT EMPLOYED", "NONE", "SELF EMPLOYED", "N", "NOT EMPLOYED", "HOMEMAKER", "N", "SELF", "RETIRED", "REQUESTED", "SELF-EMPLOYED", "REQUESTED", "NONE","SELF-EMPLOYED","SELF EMPLOYED","INFO REQUESTED","INFO REQUESTED","HOMEMAKER","INFORMATION REQUESTED (BEST EFFORTS)","INFORMATION REQUESTED PER BEST EFFO","NOT EMPLOYED","STUDENT","HOUSEWIFE","NA","UNEMPLOYED","SELF EMPLOYED","RE","SELFEMPLOYED","NA","SELFEMPLOYED","RET."]

donors.replace(to_replace={"employer":non_employers}, value="", inplace=True)

donors["donor_id"] = donors.contributor_ext_id

#count = 1674990
sums = donors.groupby(by=["donor_id"])["amount"].sum()
donors.drop("amount", axis=1, inplace=True)
donors.set_index("donor_id", inplace=True)
donors = donors.join(sums)
donors["donor_id"] = donors.index
donors.drop_duplicates(subset=["donor_id"], inplace=True)
donors.drop("donor_id", axis=1, inplace=True)
donors.reset_index(inplace=True)
donors.drop("donor_id", axis=1, inplace=True)
#count = 743134
donors = donors[donors.last_name.str.len() > 1]
donors = donors[donors.first_name.str.len() > 1]
#count = 727870

donors = donors[donors.amount > 0]
#count = 727405

prospects = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/prospects.txt",sep="\t", usecols=["name","id","url"])
prospects = prospects[prospects["name"].str.find(" ") > -1]
prospects["first_name"] = prospects["name"].apply(lambda f: f.split(" ")[0].upper())
prospects["last_name"] = prospects["name"].apply(lambda f: f.split(" ")[-1].upper())

donors_merged = donors.merge(prospects, how="inner", on=["first_name","last_name"])
#count unique = 483810
prospects = None

#zip to coords
zips = pandas.read_csv("zipcode.csv")
zips.rename(columns={"zip":"contributor_zipcode","latitude":"contributor_lat","longitude":"contributor_lng"}, inplace=True)
zips = zips[["contributor_zipcode","contributor_lat","contributor_lng"]]

#prospect id to coords
prospect_latlngs = pandas.read_csv("prospects_with_lat_lng.csv", names=["prospect_id","location_id","lat","lng"], sep="\t")
donors_merged.rename(columns={"id":"prospect_id"}, inplace=True)
donors_merged = donors_merged.merge(prospect_latlngs, how="inner", on=["prospect_id"])
#count unique = 472993
donors_merged = donors_merged.merge(zips, how="inner", on=["contributor_zipcode"])
#count unique = 466911

#calculate distance
donors_merged["distance_miles"] = donors_merged.apply(lambda row: vincenty((row.contributor_lat, row.contributor_lng), (row.lat, row.lng)).miles, axis=1)
donors_merged_subset = donors_merged[donors_merged.distance_miles <= 100]
#count unique = 237971

#subset to only those with 1 match in contributor dataset
counts = donors_merged_subset.contributor_ext_id.value_counts()
onematch = counts[counts ==1].index.values
donors_merged_onematch = donors_merged_subset[donors_merged_subset.contributor_ext_id.isin(onematch)]
#count unique = 143747

#subset to only those with 1 match in linkedin
counts = donors_merged_onematch.prospect_id.value_counts()
onematch = counts[counts ==1].index.values
donors_merged_onematch = donors_merged_onematch[donors_merged_onematch.prospect_id.isin(onematch)]
#count unique = 136326

#remove extreme outliers
donors_merged_onematch = donors_merged_onematch[donors_merged_onematch.amount <100000]
#count = 135923

donors_merged_onematch.to_csv("donors_merged_onematch.csv", index=None)
