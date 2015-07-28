import datetime
import requests
from prime.utils import headers
import json, pandas
from prime.prospects.models import PiplEmail, Prospect
from prime.prospects.get_prospect import session, from_linkedin_id, from_url, average_wealth_score
from prime.utils import r
from prime.utils.googling import *
from prime.utils.networks import *

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

#176
search_urls = set()
for index, row in df.iterrows():
	terms = row.FirstName + " " + row.LastName + " " + row.Company + " " + row.JobTitle
	name = row.FirstName + " " + row.LastName
	email = row.EmailAddress
	pipl_rec = session.query(PiplEmail).get(email)
	if not pipl_rec or not pipl_rec.linkedin_url:
		url = search_linkedin_profile(terms,name)
		if url:
			prospect = from_url(url)
			if prospect and prospect.updated != datetime.date.today(): 
				r.sadd("urls",url)
				print url
			search_urls.add(url)

friend_recs=0
rescrape = set()
jaime_friends = set()
#176 search urls
#173 friends
for url in search_urls:
	friend = from_url(url)
	if friend: 
		jaime_friends.add(friend.linkedin_id)
		friend_recs+=1
	else:
		rescrape.add(url)

pipl_recs =0
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

boosted_ids = set(jaime_json.get("boosted_ids"))
for friend in jaime_friends:
    if friend>1: boosted_ids.add(str(friend))

jaime_json["boosted_ids"] = list(boosted_ids)
session.query(Prospect).filter_by(id=jaime.id).update({"json": jaime_json})
session.commit()

friends = jaime.json.get("boosted_ids")
#433 scraped and id'd. average wealth score: 64

#224
new_york_employed = agent_network(friends)

#nothing really stands out here
industries = {}
for prospect in new_york_employed:
    industry = prospect.industry_raw
    count = industries.get(industry) 
    if count is None: count = 0
    count += 1
    industries[industry] = count
print sorted(industries, key=industries.get, reverse=True)


from consume.get_gender import get_firstname, get_gender
#{None: 25, 'Female': 105, 'Male': 65}
genders = {}
for prospect in new_york_employed:
    gender = get_gender(get_firstname(prospect.name))
    if gender==True: gender = 'Male'
	if gender==False: gender = 'Female' 
    count = genders.get(gender) 
    if count is None: count = 0
    count += 1
    genders[gender] = count

groups = {}
for prospect in new_york_employed:
	if not prospect.json: continue
	pgroups = prospect.json.get("groups")
	for group in pgroups:
		count = groups.get(group.get("name")) 
		if count is None: count = 0
		count += 1
		groups[group.get("name")] = count

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
    if skills[skill]>45: print skill + ": " + str(skills[skill])

interests = {}
for prospect in new_york_employed:
	if not prospect.json: continue
	pinterests = prospect.json.get("interests")
	if not pinterests: continue
	for interest in pinterests:
		count = interests.get(interest) 
		if count is None: count = 0
		count += 1
		interests[interest] = count
for interest in interests.keys():
    if interests[interest]>10: print interest + ": " + str(interests[interest])

companies = {}
for prospect in new_york_employed:
	company = prospect.current_job.company.name
	count = companies.get(company) 
	if count is None: count = 0
	count += 1
	companies[company] = count
for company in companies.keys():
    if companies[company]>10: print company + ": " + str(companies[company])

#6 people -- all financial services and not local
#u = search_extended_network(jaime, limit=300)

#extended_network = {}
for prospect in new_york_employed:
	if extended_network.get(prospect.url) is None:
		u = search_extended_network(prospect, limit=300)
		extended_network.update({prospect.url: u})

#average age is 38
from dateutil.relativedelta import relativedelta
has_college = 0
total_age = 0
count_for_age = 0
schools = {}
for prospect in new_york_employed:
	grad, school = collegeGrad(prospect)
	if school:
		has_college += 1
		count = schools.get(school)
		if count is None: count = 0
		count += 1
		schools[school] = count		
		if grad: 
			difference_in_years = relativedelta(datetime.date.today(), grad).years
			#print str(difference_in_years) + " " + prospect.url
			age = difference_in_years + 24
			total_age += age
			count_for_age += 1
	
def collegeGrad(prospect):
	vals = None, None
	for education in prospect.schools: 
		if education.school_linkedin_id and education.end_date: 
			return education.end_date, education.linkedin_school.name
	for education in prospect.schools: 
		if education.school_linkedin_id: 
			return None, education.linkedin_school.name			
	return vals

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
	if prospect.image_url: secret_score = score + 1 
	else: secret_score = score
	d = {"id":prospect.id, "name":prospect.name, "job":prospect.current_job.title, "company":prospect.current_job.company.name, "score":score, "image_url": prospect.image_url if prospect.image_url else "", "url":prospect.url, "secret_score" : secret_score}
	demo.append(d)
demo = sorted(demo, key=lambda k: k['secret_score'], reverse=True)
print json.dumps(demo)	
