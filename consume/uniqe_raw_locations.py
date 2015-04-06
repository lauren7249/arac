import re, sys, os, pandas

def clean(str):
    if str:
    	str = re.sub("\n"," ", str)
        return re.sub("\s+"," ",str.lower())
    return None

def process_files(prospectpath, jobpath, outputfile):
	p = pandas.read_csv(prospectpath,names=["id","raw_location"], header=None, sep=',', usecols=["raw_location"])
	j = pandas.read_csv(jobpath,names=["id","raw_location"], header=None, sep=',', usecols=["raw_location"])
	df = p.append(j)
	p = None
	j = None
	df.fillna("",inplace=True)
	df.drop_duplicates(inplace=True, subset="raw_location")
	df["raw_location"] = df["raw_location"].apply(clean)
	df.drop_duplicates(inplace=True, subset="raw_location")
	df.to_csv(path_or_buf=outputfile,header=False, index=False)

#run this first to get unique dirty locations with trivial cleaning
#then run clean_locations 
#then run map_locations
if __name__ == '__main__':

	path = sys.argv[1]
	locations_path = path + "unique_dirty_locations.csv"	

	prospect_locations_path = 	path + "prospect_locations.csv"
	job_locations_path = 		path + "job_locations.csv"

	if os.path.isfile(locations_path): os.remove(locations_path)

	unique_locations = open(locations_path,'ab')
	process_files(prospect_locations_path, job_locations_path, unique_locations)
