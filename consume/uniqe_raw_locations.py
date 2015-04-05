import requests, re, geocoder, sys, os, multiprocessing

def clean(str):
    if str:
        return re.sub("\s+"," ",str.lower())
    return None

def process_file(inputfile, outputfile, unique_locations_set):
	while True:
		line = inputfile.readline()
		if not line: break
		line = line.rstrip()
		raw_location = clean(line[line.find(",")+1:])
		if raw_location is not None and raw_location not in unique_locations_set:
			unique_locations_set.add(raw_location)
			outputfile.write(raw_location + "\n")
	return unique_locations_set

if __name__ == '__main__':
	#path =  "/var/folders/x7/h_27fz_13f3dly9n_3wywqzc0000gn/T/sublime-sftp-browse-1428083655/sftp-config.json/mnt/big"
	path = sys.argv[1]
	locations_path = path + "unique_locations.csv"	

	prospect_locations_path = 	path + "prospect_locations.csv"
	job_locations_path = 		path + "job_locations.csv"

	if os.path.isfile(locations_path): os.remove(locations_path)

	unique_locations = open(locations_path,'ab')
	prospect_locations = open(prospect_locations_path,"rb")
	job_locations = open(job_locations_path,"rb")

	unique_locations_set = set([])
	unique_locations_set = process_file(prospect_locations, unique_locations, unique_locations_set)
	unique_locations_set = process_file(job_locations, unique_locations, unique_locations_set)

	unique_locations.close()

	print len(unique_locations_set)