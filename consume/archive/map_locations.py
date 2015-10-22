import re, sys, os, pandas, multiprocessing

def clean(str):
    if str:
    	str = re.sub("\n"," ", str)
        return re.sub("\s+"," ",str.lower())
    return None

def get_location_id(raw_location):
	raw_location = clean(raw_location)
	location_id = raw_xwalk_clean_dict.get(raw_location)	
	return location_id

def process_file(inputpath, outputpath):
	df = pandas.read_csv(inputpath,names=["id","raw_location"], header=None, sep=',')
	df.fillna("",inplace=True)
	df["location_id"] = df["raw_location"].apply(get_location_id)
	df.to_csv(path_or_buf=outputpath, columns=["id","location_id"], header=False, index=False)

if __name__ == '__main__':
	path = sys.argv[1]

	#intermediary crosswalk file
	raw_xwalk_clean_path = "raw_xwalk_clean.csv"

	#original files
	prospect_locations_path = 	path + "prospect_locations.csv"
	job_locations_path = 		path + "job_locations.csv"

	#output files
	prospect_location_ids_path = path + "prospect_location_ids.csv"
	job_location_ids_path = path + "job_location_ids.csv"

	#delete output files
	if os.path.isfile(prospect_location_ids_path): os.remove(prospect_location_ids_path)
	if os.path.isfile(job_location_ids_path): os.remove(job_location_ids_path)

	#turn intermediary crosswalk into dict
	raw_xwalk_clean_df = pandas.read_csv(raw_xwalk_clean_path,names=["raw_location","location_id"], header=None, sep=',')
	raw_xwalk_clean_df.fillna("",inplace=True)
	raw_xwalk_clean_df[raw_xwalk_clean_df["location_id"].str.contains('[A-Za-z]')] = ""
	raw_xwalk_clean_df = raw_xwalk_clean_df[raw_xwalk_clean_df.location_id != ""]

	global raw_xwalk_clean_dict
	raw_xwalk_clean_dict = dict(zip(raw_xwalk_clean_df["raw_location"], raw_xwalk_clean_df["location_id"]))

	process_file(prospect_locations_path, prospect_location_ids_path)
	process_file(job_locations_path, job_location_ids_path)
	

