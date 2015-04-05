import re, sys, os, pandas

def clean(str):
    if str:
        return re.sub("\s+"," ",str.lower())
    return None

def process_file(inputpath, outputpath, raw_xwalk_clean_dict):
	outputfile = open(outputpath,"ab")
	df = pandas.read_csv(inputpath,names=["id","raw_location"], header=None, sep=',')
	df.fillna("",inplace=True)
	for index, row in df.iterrows():
		location_id = None
		raw_location = None
		raw_location = clean(row["raw_location"])
		if raw_location: raw_location = re.sub('"','',raw_location)
		location_id = raw_xwalk_clean_dict.get(raw_location)
		if location_id: outputfile.write(str(row["id"]) + "," + str(location_id) + "\n")
		else: outputfile.write(str(row["id"]) + "," + "\n")
	outputfile.close()

if __name__ == '__main__':
	path = sys.argv[1]

	#original files
	prospect_locations_path = 	path + "prospect_locations.csv"
	job_locations_path = 		path + "job_locations.csv"

	#intermediary crosswalk files
	locations_norm_path = 	path + "locations_norm.csv"	
	raw_xwalk_clean_path =	path + "raw_xwalk_clean.csv"

	#output files
	prospect_location_ids_path = path + "prospect_location_ids.csv"
	job_location_ids_path = path + "job_location_ids.csv"
	locations_path = path + "locations.csv"

	#delete output files
	if os.path.isfile(prospect_location_ids_path): os.remove(prospect_location_ids_path)
	if os.path.isfile(job_location_ids_path): os.remove(job_location_ids_path)
	if os.path.isfile(locations_path): os.remove(locations_path)

	'''
	#dedupe locations	
	locations_norm_df = pandas.read_csv(locations_norm_path,names=["location_id","location_name","lat","lng"], header=None, sep=',')
	locations_norm_df.drop_duplicates(inplace=True, subset="location_id")
	locations_norm_df.to_csv(path_or_buf=locations_path, index=False)
	'''

	#turn intermediary crosswalk into dict
	raw_xwalk_clean_df = pandas.read_csv(raw_xwalk_clean_path,names=["raw_location","location_id"], header=None, sep=',')
	raw_xwalk_clean_df.fillna("",inplace=True)
	raw_xwalk_clean_df[raw_xwalk_clean_df["location_id"].str.contains('[A-Za-z]')] = ""
	raw_xwalk_clean_df = raw_xwalk_clean_df[raw_xwalk_clean_df.location_id != ""]
	raw_xwalk_clean_dict = dict(zip(raw_xwalk_clean_df["raw_location"], raw_xwalk_clean_df["location_id"]))

	process_file(prospect_locations_path, prospect_location_ids_path, raw_xwalk_clean_dict)
	process_file(job_locations_path, job_location_ids_path, raw_xwalk_clean_dict)
	

