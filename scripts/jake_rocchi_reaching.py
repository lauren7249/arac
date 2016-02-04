from spark.hbase_load_simple import HBaseLoader
from helpers.stringhelpers import name_match
from helpers.linkedin_helpers import get_dob_year_range
from prime.utils.crawlera import reformat_crawlera
import numpy, json
from prime.processing_service.geocode_service import GeocodeRequest, GeoPoint, MapQuestRequest
import happybase
from prime.processing_service.pipl_request import PiplRequest
from prime.processing_service.social_profiles_service import SocialProfilesRequest
from prime.processing_service.profile_builder_service import wrapper as profile_builder

hb = HBaseLoader("2016_01",sc)
data = hb.get_s3_data()
local_locations_raw = ["New York, New York","Boston, MA","Hartford, Connecticut","Washington, DC"]
local_locations = []
for location in local_locations_raw:
    local_locations.append(MapQuestRequest(location).process())

def for_jake(line):
    linkedin_data = json.loads(line)
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
    lead_location = GeocodeRequest(linkedin_data).process()
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
            return [linkedin_data]   
    return []

datamap = data.flatMap(for_jake)
datamap.cache()
#15 minutes!! - 7023 people
output_data = datamap.collect()

def enrich(linkedin_data):
    url = linkedin_data.get("canonical_url")
    if url:
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
    person = {"linkedin_data":linkedin_data}
    return SocialProfilesRequest(person).process()

enriched = datamap.map(enrich)
enriched.cache()
enriched_output = enriched.collect()
profiles = enriched.map(profile_builder)
profiles.cache()
profiles_output = profiles.collect()



