file = open("/mnt/big/clean_job_location_ids.csv", "r")
write_file = open("/mnt/big/veryclean_job_location_ids.csv", "a+")

for line in file:
    item = line.split(",")[1]
    if item.startswith("somer"):
        pass
    else:
        write_file.write(line)
