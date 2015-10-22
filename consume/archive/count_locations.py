import pandas, numpy

prospect_location_ids = pandas.read_csv('/mnt/big/prospect_location_ids.csv', names=["id","location_id"], header=None, index_col="location_id", dtype={"location_id":numpy.float64})
locations = pandas.read_csv('/mnt/big/locations.csv', sep=',', index_col="location_id", usecols=["location_id","location_name"],dtype={"location_id":numpy.float64}))
counts = prospect_location_ids.index.value_counts()
counts = pandas.DataFrame(counts)
counts.columns = ["count"]
location_counts = counts.join(locations)
location_counts.sort(columns="count",ascending=False, inplace=True)
location_counts["location_id"] = location_counts.index
location_counts.location_id = location_counts.location_id.apply(lambda x: x.astype(int))
location_counts.to_csv("/mnt/big/prospect_location_counts.csv", index=False,columns=["location_id","location_name","count"], header=False)
