import requests
import lxml.html
from prime.utils import headers
import pandas
import re

pipl_api_key = "uegvyy86ycyvyxjhhbwsuhj9"
vibe_api_key = "e0978324d7ac8b759084aeb96c5d7fde"
fullcontact_api_key = "dda7318aacfcf5cd"
pipl_url ="http://api.pipl.com/search/v3/json/?key=" + pipl_api_key + "&pretty=true"
vibe_url = "https://vibeapp.co/api/v1/initial_data/?api_key=" + vibe_api_key + "&email="
fullcontact_url = "http://api.fullcontact.com/v2/person.json?apiKey=" + fullcontact_api_key 
social_domains = ["twitter","soundcloud","slideshare","plus","pinterest","facebook","linkedin","amazon"]  

zillow = pandas.read_csv("/Users/lauren/Downloads/Zip_ZriPerSqft_AllHomes.csv")

def get_pipl_emails(pipl_json):
    emails = []
    if not pipl_json: return emails
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("emails"): continue
        for email in record.get("emails"):
            url = email.get("address") 
            if url and url not in emails: 
                emails.append(url)
    return emails

def get_pipl_images(pipl_json):
    images = []
    if not pipl_json: return images
    for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
        if not record.get('@query_params_match',True) or not record.get("emails"): continue
        for image in record.get("images"):
            url = image.get("url") 
            if url and url not in images: 
                try:
                    response = requests.get(url,headers=headers)
                    if response.status_code==200: images.append(url)
                except:
                    pass
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
        for address in record.get("addresses"):
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
        for address in record.get("addresses"):
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

def get_vibe_social_accounts(vibe_json):
    social_profiles = []
    if not vibe_json or not vibe_json.get("social_profiles"): return social_profiles
    for record in vibe_json.get("social_profiles"):
        link = record.get("url")
        social_profiles.append(link)    
    return social_profiles

def get_fullcontact_social_accounts(fullcontact_json):
    social_profiles = []
    if not fullcontact_json or not fullcontact_json.get("socialProfiles") or fullcontact_json.get("likelihood") < 0.75: return social_profiles
    for record in fullcontact_json.get("socialProfiles"):
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
        pass
    return None
