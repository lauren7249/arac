import requests
from prime.utils import headers
import json, pandas
from prime.prospects.models import PiplEmail, Prospect
from prime.prospects.get_prospect import session, from_linkedin_id, from_url, average_wealth_score
from prime.utils import r
from prime.utils.googling import *

pipl = "http://api.pipl.com/search/v3/json/?key=uegvyy86ycyvyxjhhbwsuhj9&pretty=true&email="

jaime = from_linkedin_id("6410262")
df = pandas.read_csv("/Users/lauren/Documents/jaimekorbin.csv", delimiter="\t")
df.fillna("", inplace=True)
email_list = list(df.EmailAddress)

#695
jaime_json = jaime.json
jaime_json["email_contacts"] = email_list
session.query(Prospect).filter_by(id=jaime.id).update({"json": jaime_json})
session.commit()


#343 profiles
#318 unique pipl linkedin profiles
for email in jaime.email_contacts:
	if session.query(PiplEmail).get(email) is None:
		print email
		req = pipl + email
		response = requests.get(req, headers=headers, verify=False)
		if response.status_code == 200:
			pipl_json = json.loads(response.content)
			linkedin_url = None
			for record in pipl_json.get("records"):
				if record.get('@query_params_match') and not record.get("source").get("@is_sponsored") and record.get("source").get("domain") == "linkedin.com":
					linkedin_url = record.get("source").get("url")
					r.sadd("urls",linkedin_url) #for scraper
					break
			piplrecord = PiplEmail(email=email, linkedin_url=linkedin_url, pipl_response=pipl_json)
			session.add(piplrecord)
			session.commit()

search_urls = set()
for index, row in df.iterrows():
	terms = row.FirstName + " " + row.LastName + " " + row.Company + " " + row.JobTitle
	name = row.FirstName + " " + row.LastName
	email = row.EmailAddress
	pipl_rec = session.query(PiplEmail).get(email)
	if not pipl_rec or not pipl_rec.linkedin_url:
		url = search_linkedin_profile(terms,name)
		r.sadd("urls",url)
		search_urls.add(url)
		
jaime_friends = set()
pipl_recs =0
friend_recs=0
rescrape = set()
for email in jaime.email_contacts:
	pipl_rec = session.query(PiplEmail).get(email)
	if pipl_rec: 
		pipl_recs+=1
		linkedin_url = pipl_rec.linkedin_url
		friend = from_url(linkedin_url)
		if friend: 
			jaime_friends.add(friend.linkedin_id)
			friend_recs+=1
		else:
			rescrape.add(linkedin_url)

boosted_ids = []
for friend in jaime_friends:
    if friend>1: boosted_ids.append(str(friend))

jaime_json["boosted_ids"] = boosted_ids
session.query(Prospect).filter_by(id=jaime.id).update({"json": jaime_json})
session.commit()

#263 scraped and id'd. average wealth score: 64
prospects = []
for friend in jaime.json.get("boosted_ids"):
	prospect = from_linkedin_id(friend)
	prospects.append(prospect)


#195 NY friends
#161 employed 
#152 not in financial services
#average wealth score 63
new_york_employed = []
states = {}
for prospect in prospects:
	if prospect.current_job is None: continue
    key = prospect.location_raw.split(",")[-1].strip()
    if key in ['New York','Greater New York City Area'] and prospect.industry_raw not in ['Insurance','Financial Services']: new_york_employed.append(prospect)
	count = states.get(key) 
	if count is None: count = 0
	count += 1
	states[key] = count    

#nothing really stands out here
industries = {}
for prospect in new_york_employed:
    industry = prospect.industry_raw
    count = industries.get(industry) 
    if count is None: count = 0
    count += 1
    industries[industry] = count
print sorted(industries, key=industries.get, reverse=True)


industries = {}
for prospect in new_york_employed:
    industry = prospect.industry_raw
    count = industries.get(industry) 
    if count is None: count = 0
    count += 1
    industries[industry] = count

from consume.get_gender import get_firstname, get_gender
#{None: 14, 'Female': 87, 'Male': 51}
genders = {}
for prospect in new_york_employed:
    gender = get_gender(get_firstname(prospect.name))
    if gender==True: gender = 'Male'
	if gender==False: gender = 'Female' 
    count = genders.get(gender) 
    if count is None: count = 0
    count += 1
    genders[gender] = count

skills = {}
for prospect in new_york_employed:
	if not prospect.json: continue
	pskills = prospect.json.get("skills")
	for skill in pskills:
		count = skills.get(skill) 
		if count is None: count = 0
		count += 1
		skills[skill] = count
for skill in skills.keys():
    if skills[skill]>15: print skill + ": " + str(skills[skill])

#6 people -- all financial services and not local
#u = search_extended_network(jaime, limit=300)

#extended_network = {}
for prospect in new_york_employed:
	if extended_network.get(prospect.url) is None:
		u = search_extended_network(prospect, limit=300)
		extended_network.update({prospect.url: u})

def leadScore(prospect):
	valid_school = False
	for education in prospect.schools: 
		if education.school_linkedin_id: valid_school = True
	if not valid_school and not prospect.image_url and prospect.connections < 500: return 1
	if valid_school and prospect.image_url and prospect.connections==500: return 3
	return 2

demo = []
for prospect in new_york_employed:
	score = leadScore(prospect)
	d = {"id":prospect.id, "name":prospect.name, "job":prospect.current_job.title, "company":prospect.current_job.company.name, "score":score}
	demo.append(d)
