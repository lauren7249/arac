from spark.hbase_load_simple import HBaseLoader
from helpers.stringhelpers import name_match
from helpers.linkedin_helpers import get_dob_year_range
from prime.utils.crawlera import reformat_crawlera
import numpy, json, re
from prime.processing_service.geocode_service import GeocodeRequest, GeoPoint, MapQuestRequest
import happybase
from prime.processing_service.pipl_request import PiplRequest
from prime.processing_service.lead_service import LeadService

from prime.processing_service.glassdoor_service import wrapper as glassdoor_calc
from prime.processing_service.indeed_service import wrapper as indeed_calc
from prime.processing_service.age_service import wrapper as age_calc
from prime.processing_service.gender_service import wrapper as gender_calc
from prime.processing_service.college_degree_service import wrapper as college_degree_calc
from prime.processing_service.social_profiles_service import wrapper as social_profiles_calc
from prime.processing_service.phone_service import wrapper as phone_calc
from prime.processing_service.profile_builder_service import wrapper as profile_builder_calc
from prime.processing_service.scoring_service import ScoringService, wrapper as scoring_calc
from prime.processing_service.results_service import ResultService

hb = HBaseLoader("2016_01",sc)
data = hb.get_s3_data()
local_locations_raw = ["New York, New York","Boston, MA","Hartford, Connecticut","Washington, DC"]
local_locations = []
for location in local_locations_raw:
    local_locations.append(MapQuestRequest(location).process())

client_data = {'to_email': u'jeff@advisorconnect.co', 'suppress_emails': True, 'first_name': u'Jacob', 'last_name': u'Rocchi', 'location': 'Washington, D.C.', 'url': 'https://www.linkedin.com/in/jacobrocchi', 'email': u'jake_rocchi@advisorconnect.co', 'hired': True}

def for_jake(line):
    try:
        linkedin_data = json.loads(line)
    except:
        return []
    url = linkedin_data.get("canonical_url")
    if not url:
        return []
    same_school = False
    for school in linkedin_data.get("education",[]):
        if school.get("profile_url") == "http://www.linkedin.com/edu/school?id=18068":
            same_school = True
            break
        if school.get("profile_url"):
            continue
        if not school.get("name"):
            continue
        if school.get("name").lower().find("fairfield")>-1 and school.get("name").lower().find("prep")>-1 and school.get("name").lower().find("fairfield")<school.get("name").lower().find("prep"):
            same_school = True
            break
    if not same_school:
        return []
    linkedin_data = reformat_crawlera(linkedin_data)
    educations = linkedin_data.get("schools",[])
    experiences = linkedin_data.get("experiences",[])
    dob_year_range = get_dob_year_range(educations, experiences)
    if not max(dob_year_range):
        return []
    dob_year_mid = numpy.mean(dob_year_range)
    age = 2016 - dob_year_mid
    if age<22 or age>40:
        return []
    location_raw = linkedin_data.get("location")
    lead_location = GeocodeRequest(location_raw).process()
    if not lead_location:
        return []
    latlng =lead_location.get("latlng")
    if not latlng:
        return []
    geopoint = GeoPoint(latlng[0],latlng[1])
    for location in local_locations:
        latlng = location.get("latlng")
        lead_geopoint = GeoPoint(latlng[0],latlng[1])
        miles_apart = geopoint.distance_to(lead_geopoint)
        if miles_apart < 75:
            print linkedin_data.get("location")
            connection = happybase.Connection('172.17.0.2')
            data_table = connection.table('url_xwalk')
            row = data_table.row(url)
            linkedin_id = row.get("keys:linkedin_id")
            connection.close()
            if linkedin_id:
                linkedin_data["linkedin_id"] = linkedin_id
            else:
                pipl_data = PiplRequest(url, type="url").process()
                linkedin_id = pipl_data.get("linkedin_id")
                if linkedin_id:
                    linkedin_data["linkedin_id"] = linkedin_id
            return [{"linkedin_data":linkedin_data, "location_coordinates": lead_location}]
    return []

def qualified(person):
    n_connections = person.get("linkedin_data",{}).get("connections","0")
    try:
        if n_connections and int(re.sub('[^0-9]','',n_connections))<30:
            return []
    except Exception, e:
        print str(e)
        return []
    lead_service = LeadService(client_data, None)
    same_person = lead_service._is_same_person(person)
    if same_person:
        #print "SAME PERSON " + str(person)
        return []
    competitor = lead_service._is_competitor(person)
    if competitor:
        #print "COMPETITOR " + str(person)
        return []
    salary = lead_service._filter_salaries(person)
    if not salary:
        #print "SALARY PROBLEM " + str(person)
        return []
    return [person]

enriched = data.flatMap(for_jake).map(glassdoor_calc).map(indeed_calc).flatMap(qualified).map(age_calc).map(gender_calc).map(college_degree_calc).map(social_profiles_calc).map(phone_calc).map(profile_builder_calc).map(scoring_calc)
enriched.cache()
enriched_output = enriched.collect()

scoring_service = ScoringService({}, {})
scoring_service.output = enriched_output
scored_output = scoring_service.compute_stars()

#delete the old ones first
results_service = ResultService(client_data, scored_output)
results_service.process()





