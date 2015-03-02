def get_file_path(school_id=None, year=None, degree=None, prospect_id=None):
	if prospect_id is None:
		if school_id is not None:
			if degree is None:
				if year is None:
					return "entities/schools/" + str(school_id) + "/all.csv"
				else:
					return "entities/schools/" + str(school_id) + "/year_" + str(year) +  ".csv"
			else:
				if year is None:
					return "entities/schools/" + str(school_id) + "/degree_" + degree + ".csv"
				else:
					return "entities/schools/" + str(school_id) + "/year_" + str(year) + "_degree_" + degree + ".csv"
	else:
		if school_id is not None:
			if degree is None:
				if year is None:
					return "by_prospect_id/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + ".csv"
				else:
					return "by_prospect_id/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_year_" + str(year) + ".csv"
			else:
				if year is None:
					return "by_prospect_id/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_degree_" + degree
				else:
					return "by_prospect_id/" + str(prospect_id) + "/processed_school_id_" + str(school_id) + "_year_" + str(year) + "_degree_" + degree
	return None