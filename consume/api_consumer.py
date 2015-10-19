import requests
import lxml.html
from prime.utils import headers
import pandas
import re
import clearbit

vibe_api_keys = ["e0978324d7ac8b759084aeb96c5d7fde","acae5996e72c52835b0b15ed48208129",'b2acf1eadef73f4aeda890e0571f3e06']
clearbit.key='f2512e10a605e3dcaff606205dbd3758'
pipl_api_key = "uegvyy86ycyvyxjhhbwsuhj9"
pipl_api_key_basic = "ml2msz8le74d4nno7dyk0v7c"
fullcontact_api_key = "dda7318aacfcf5cd"
fullcontact_url = "http://api.fullcontact.com/v2/person.json?apiKey=" + fullcontact_api_key 
social_domains = ["twitter","soundcloud","slideshare","plus","pinterest","facebook","linkedin","amazon","angel","foursquare","github"]

#zillow = pandas.read_csv("/Users/lauren/Downloads/Zip_ZriPerSqft_AllHomes.csv")

def get_pipl_emails(pipl_json):
    emails = []
    if not pipl_json: return emails
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("emails"): continue
        for email in record.get("emails",[]):
            url = email.get("address") 
            domain = url.split("@")[-1]
            if url and url not in emails and domain != 'facebook.com': 
                emails.append(url)
    return emails

def get_pipl_images(pipl_json):
    images = []
    if not pipl_json: return images
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("emails"): continue
        for image in record.get("images",[]):
            url = image.get("url") 
            if url and url not in images and url.find("gravatar.com")==-1: 
                # try:
                #     response = requests.head(url,headers=headers, timeout=1.5)
                #     if response.status_code==404: 
                #         continue
                # except:
                #     pass
                images.append(url)
    return images

def get_pipl_zips(pipl_json):
    zips = []
    if not pipl_json: return locations
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("tags"): continue
        for tag in record.get("tags"):
            if not tag.get("@classification","") == 'zip': continue
            zip = tag.get("content")
            if zip not in zips: zips.append(zip)
    return zips

def get_pipl_addresses(pipl_json):
    locations = []
    if not pipl_json: return locations
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("addresses"): continue
        for address in record.get("addresses",[]):
            display =  address.get("display")
            if display and display not in locations: locations.append(display)
    return locations

def get_pipl_cities(pipl_json):
    locations = []
    if not pipl_json: return locations
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        #if record.get('@query_params_match'): pprint.pprint(record)
        if not record.get('@query_params_match',True) or not record.get("addresses"): continue
        # if record.get("source") and not record.get("source").get("@is_sponsored") and record.get("addresses"): print record.get("source").get("url")
        for address in record.get("addresses",[]):
            if not address.get("state"): continue
            display = address.get("state")
            if address.get("city"): display = address.get("city") + ", " + display 
            if display not in locations: locations.append(display)
    return locations

def get_pipl_social_accounts(pipl_json):
    social_profiles = []
    if not pipl_json: return social_profiles
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("source") or not record.get("source").get("url") or record.get("source").get("@is_sponsored"): continue
        link = record.get("source").get("url")
        social_profiles.append(link)    
    return social_profiles

def get_clearbit_social_accounts(clearbit_json):
    social_profiles = []
    if not clearbit_json: return social_profiles
    for key in clearbit_json.keys():
        if clearbit_json[key] and isinstance(clearbit_json[key], dict) and clearbit_json[key].get("handle"):
            handle = clearbit_json[key].get("handle")
            if key=='angellist': 
                link = "https://angel.co/" + handle
            elif key=='foursquare': 
                link = "https://" + key + ".com/user/" + handle            
            elif key=='googleplus': 
                link = "https://plus.google.com/" + handle
            else: 
                link = "https://" + key + ".com/" + handle
            social_profiles.append(link)
    return social_profiles

def get_vibe_social_accounts(vibe_json):
    social_profiles = []
    if not vibe_json or not vibe_json.get("social_profiles"): return social_profiles
    for record in vibe_json.get("social_profiles",[]):
        link = record.get("url")
        social_profiles.append(link)    
    return social_profiles

def get_fullcontact_social_accounts(fullcontact_json):
    social_profiles = []
    if not fullcontact_json or not fullcontact_json.get("socialProfiles") or fullcontact_json.get("likelihood") < 0.75: return social_profiles
    for record in fullcontact_json.get("socialProfiles",[]):
        link = record.get("url")
        social_profiles.append(link)    
    return social_profiles

def get_specific_url(social_accounts, type="linkedin.com"):
    for account in social_accounts:
        if account.find(type) > -1: return account
    return None

def get_indeed_salary(title, location=None):
    url =  "http://www.indeed.com/salary?q1=%s&l1=%s" % (title, location) if location else "http://www.indeed.com/salary?q1=%s" % (title) 
    try:
        response = requests.get(url, headers=headers)
        clean = lxml.html.fromstring(response.content)
        salary = clean.xpath("//span[@class='salary']")[0].text
        return int(re.sub('\D','', salary))
    except Exception, err:
        print title + " not found by indeed"
    return None

def get_glassdoor_salary(title):
    if not title: return None
    url =  "http://www.glassdoor.com/Salaries/" +  title.replace(" ",'-').strip() + "-salary-SRCH_KO0," + str(len(title.strip())) + ".htm"
    try:
        response = requests.get(url, headers=headers)
        clean = lxml.html.fromstring(response.content)
    except:
        print "bad request"
        return None
    try:
        salary = clean.xpath("//div[@class='meanPay nowrap positive']")[0].text_content()
        return int(re.sub('\D','', salary))
    except Exception, err:
        listings = clean.xpath(".//span[@class='i-occ strong noMargVert ']")
        if not listings: return None
        common = None
        for listing in listings:
            text = re.sub('[^a-z]',' ', listing.text.lower())
            words = set(text.split())
            common = common & words if common else words
        if not common: return None
        new_title = " ".join([w for w in text.split() if w in common])
        if new_title.lower().strip() == title.lower().strip(): return None
        print title + "-->" + new_title
        return get_glassdoor_salary(new_title)
    return None

def get_salary_percentile(max_salary):
    # response = requests.get("http://www.whatsmypercent.com/incomeRank.php?income=" + str(max_salary) + "&status=all%20filers", headers=headers)
    response = requests.get("http://www.shnugi.com/income-percentile-calculator/?min_age=18&max_age=100&income=" + str(max_salary),headers=headers)
    percentile = re.search('(?<=ranks at: )[0-9]+(?=(\.|\%))',response.content).group(0)
    # html = lxml.html.fromstring(response.content)
    # percentile = html.xpath(".//td")[1].text_content()
    return int(re.sub("[^0-9]","",percentile))    
