import pandas

df = pandas.read_csv("/Users/lauren/Downloads/prospect_location_counts.csv", header=None)
df.columns = ["id","name","count"]
df["country"] = df.apply(lambda row: row["name"].split(",")[-1].strip(), axis=1)
df = df[df.country=='United States']
df["location"] = df.apply(lambda row: row["name"].replace(', United States',''), axis=1)
df=df["location"]
df.drop_duplicates(inplace=True)
df.to_csv("/Users/lauren/Documents/arachnid/prime/templates/cloudsponge/geolocations.txt", header=None, index=False)