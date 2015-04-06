import pandas, requests, re, sys, os, multiprocessing

def parse_out(text, startTag, endTag):
	region = ""
	region_start = text.find(startTag)
	if region_start > -1:
		region = text[region_start+len(startTag):]
		region_end = region.find(endTag)
		if region_end > -1:
			region = region[:region_end]	
	return region

def add_lat_long(text, location):
	region_start = text.find('"lng":')
	text = text[region_start+6:]

	region = parse_out(text, '"lat":', ',')
	if len(region): location["lat"] = region	

	region = parse_out(text, '"lng":', '}')
	if len(region): location["lng"] = region	

	if location["lat"] == "null":
		location = add_lat_long(text, location)
	return location

def get_mapquest(raw):
	location = {}
	url =  "https://www.mapquest.com/?q=%s" % (raw)
	headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
	try:
		response = requests.get(url, headers=headers)
		response_text = response.content

		region = parse_out(response_text, '"countryLong":"', '","')
		if len(region): location["country"] = region	

		region = parse_out(response_text, '"region":"', '","')
		if len(region): location["region"] = region

		region = parse_out(response_text, '"locality":"', '","')
		if len(region): location["locality"] = region

		location = add_lat_long(response_text, location)
	except:
		pass
	return location


def location_string(location):
	if location is None or len(location)==0: return None
	if location.get("locality") is None:
		if location.get("region") is None:
			return location.get("country")
		else:
			return location.get("region") + ", " + location.get("country")
	else:
		if location.get("region") is None:
			return location.get("locality") + ", " + location.get("country")
		else:
			return location.get("locality") + ", " + location.get("region") + ", " + location.get("country")

def geocode(raw):
	location = get_mapquest(raw)
	return location_string(location), location

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
	