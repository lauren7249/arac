def get_file_path(school_id=None, year=None, degree=None, prospect_id=None, location=None, company_id=None):
	if prospect_id is None:
		if school_id is not None:
			if degree is None:
				if year is None:
					return "entities/educations/" + str(school_id) + "/all.csv"
				else:
					return "entities/educations/" + str(school_id) + "/year_" + str(year) +  ".csv"
			else:
				if year is None:
					return "entities/educations/" + str(school_id) + "/degree_" + str(degree) + ".csv"
				else:
					return "entities/educations/" + str(school_id) + "/year_" + str(year) + "_degree_" + str(degree) + ".csv"
		elif company_id is not None:
			if location is None:
				if year is None:
					return "entities/jobs/" + str(company_id) + "/all.csv"
				else:
					return "entities/jobs/" + str(company_id) + "/year_" + str(year) +  ".csv"
			else:
				if year is None:
					return "entities/jobs/" + str(company_id) + "/location_" + str(location) + ".csv"
				else:
					return "entities/jobs/" + str(company_id) + "/year_" + str(year) + "_location_" + str(location) + ".csv"			

	else:
		if school_id is not None:
			if degree is None:
				if year is None:
					return "entities/prospects/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + ".csv"
				else:
					return "entities/prospects/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_year_" + str(year) + ".csv"
			else:
				if year is None:
					return "entities/prospects/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_degree_" + str(degree)
				else:
					return "entities/prospects/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_year_" + str(year) + "_degree_" + str(degree)
		elif company_id is not None:
			if location is None:
				if year is None:
					return "entities/prospects/" + str(prospect_id) + "/processed_company_id_" + str(company_id) + ".csv"
				else:
					return "entities/prospects/" + str(prospect_id) + "/processed_company_id_" + str(company_id) + "_year_" + str(year) + ".csv"
			else:
				if year is None:
					return "entities/prospects/" + str(prospect_id) + "/processed_company_id_" + str(company_id) + "_location_" + str(location)
				else:
					return "entities/prospects/" + str(prospect_id) + "/processed_company_id_" + str(company_id) + "_year_" + str(year) + "_location_" + str(location)

	return None