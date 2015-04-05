import requests, re, sys, os, multiprocessing

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

def process_line(line, locations_norm_path, raw_xwalk_clean_path):
	clean_location = None
	raw_location = None
	raw_location = line.rstrip()
	if raw_location:
		clean_location, georesult = geocode(raw_location)
		if clean_location is not None:
			location_id = hash(clean_location)
			with open(raw_xwalk_clean_path,"a")	as f:
				f.write(raw_location + "," + str(location_id) + "\n")
				f.close()			
			with open(locations_norm_path,"a")	as f:
				f.write(str(location_id) + ',"' + clean_location + '",' + str(georesult.get("lat")) + "," + str(georesult.get("lng")) + '\n')
				f.close()

if __name__ == '__main__':

	path = sys.argv[1]

	locations_norm_path = 	path + "locations_norm.csv"	
	raw_xwalk_clean_path =	path + "raw_xwalk_clean.csv"

	if os.path.isfile(locations_norm_path): os.remove(locations_norm_path)
	if os.path.isfile(raw_xwalk_clean_path): os.remove(raw_xwalk_clean_path)

	pool = multiprocessing.Pool(100)

	raw_locations_path = 	path + "unique_locations.csv"
	raw_locations = open(raw_locations_path,"rb")
	while True:
		line = raw_locations.readline()
		if not line: break
		pool.apply_async(process_line, args=(line, locations_norm_path,raw_xwalk_clean_path,))

	pool.close()
	pool.join()