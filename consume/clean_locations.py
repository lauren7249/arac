import pandas, requests, re, sys, os, multiprocessing
from prime.utils.geocode import *

def process_line(raw_location):
	if raw_location is not None and type(raw_location) is str:
		clean_location, georesult = geocode(raw_location)
		if clean_location is not None:
			location_id = hash(clean_location)
			with open(raw_xwalk_clean_path,"ab") as f:
				f.write('"' + raw_location + '",' + str(location_id) + "\n")
				f.close()		

			with open(locations_path,"ab") as f:
				f.write(str(location_id) + ',"' + clean_location + '",' + str(georesult.get("lat")) + "," + str(georesult.get("lng")) + '\n')
				f.close()

if __name__ == '__main__':

	path = sys.argv[1]

	global raw_xwalk_clean_path
	global locations_path

	raw_xwalk_clean_path =	"raw_xwalk_clean.csv"
	locations_path = "locations.csv"

	if os.path.isfile(locations_path): os.remove(locations_path)
	if os.path.isfile(raw_xwalk_clean_path): os.remove(raw_xwalk_clean_path)

	pool = multiprocessing.Pool(100)

	raw_locations_path = 	path + "unique_dirty_locations.csv"

	raw_locations = list(pandas.read_csv(raw_locations_path,names=["raw_location"], header=None, sep=',',usecols=["raw_location"])["raw_location"].values)
	results = pool.map(process_line,raw_locations)

	locations_df = pandas.read_csv(locations_path,names=["location_id","location_name","lat","lng"], header=None, sep=',')
	locations_df.drop_duplicates(inplace=True, subset="location_id")
	locations_df.to_csv(path_or_buf=locations_path, index=False)	
	