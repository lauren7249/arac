from prime.utils.geocode import get_mapquest_coordinates, get_google_results
from prime.utils.bing import query, search_linkedin_companies
from prime.prospects.models import session
from prime.prospects.get_prospect import company_from_url, name_match
from consume.li_scrape_job import scrape_job
import json, re, requests
from prime.utils import headers
from consume.api_consumer import clearbit
from consume.convert import uu

def augment_company_info(contact_profiles):
    company_urls = set()
    #we get possible links to missing linkedin company pages, and possible links to extended network contacts
    for profile in contact_profiles:
        if profile.company_url:
            company_urls.add(profile.company_url)
        else: 
            urls = search_linkedin_companies(profile.company_name)
            for url in urls:
                company_urls.add(url)
    seconds_scraped, urls_scraped = scrape_job(company_urls)
    for profile in contact_profiles:
        company = None
        #try to get the linkedin company page
        if profile.company_url:
            company = company_from_url(profile.company_url)
        else: 
            urls = search_linkedin_companies(profile.company_name)
            for url in urls:
                company = company_from_url(url)
                if company: 
                    profile.company_url = url
                    session.add(profile)
                    session.commit()
                    break
        if not profile.industry and company and company.industry:
            profile.industry = company.industry
            session.add(profile)
            session.commit()
        if company:
            if company.website:
                profile.company_website = company.website
                session.add(profile)
                session.commit()            
            if company.headquarters:
                profile.company_headquarters = company.headquarters
                session.add(profile)
                session.commit()    

def get_phone_number(profile, liscraper):
    if profile.phone: 
        return profile.phone
    mapquest_coordinates = ""
    mapquest = ""
    location = profile.location if profile.location else profile.job_location
    company_name = profile.company_name 
    if not company_name:
        return None
    if profile.company_website: 
        website = profile.company_website.replace("https://","").replace("http://","").split("/")[0]
    else:
        website = ""
    if profile.company_headquarters: 
        headquarters = profile.company_headquarters.replace("\n"," ")   
    else:
        headquarters = "" 
    if location:
        mapquest = get_mapquest_coordinates(location)
        if mapquest and mapquest.get("region"): 
            mapquest_coordinates = mapquest.get("region").replace('"','')
    queries = ["+".join([company_name,mapquest_coordinates])]
    if website: queries = ["+".join([website, company_name, mapquest_coordinates]),"+".join([website,mapquest_coordinates])] + queries + ["+".join([website,company_name,headquarters]),"+".join([website,headquarters]),"+".join([company_name,headquarters]),"+".join([website, company_name]),website] 
    for q in queries:
        if q.endswith("+") or q.startswith("+"): 
            continue
        google_results = get_google_results(liscraper, q)   
        if google_results.phone_numbers and len(set(google_results.phone_numbers))==1 and len(set(google_results.plus_links))==1: 
            print uu(q)
            profile.phone = google_results.phone_numbers[0]
            session.add(profile)
            session.commit()
            return profile.phone
        elif len(google_results.phone_numbers)==len(google_results.plus_links):
            for k in xrange(0, len(google_results.plus_links)):
                plus_link = google_results.plus_links[k]
                bing_results = query("", site="%22" + plus_link + "%22").results
                if not bing_results: continue
                bing_title = bing_results[0].get("Title").replace(' - About - Google+','')
                if name_match(bing_title, company_name):
                    print uu(q)
                    profile.phone = google_results.phone_numbers[k]
                    session.add(profile)
                    session.commit()
                    return profile.phone
        else: 
            for k in xrange(0, len(google_results.plus_links)):
                plus_link = google_results.plus_links[k]
                bing_results = query("", site="%22" + plus_link + "%22").results
                if not bing_results: continue
                bing_title = bing_results[0].get("Title").replace(' - About - Google+','')
                if name_match(bing_title, company_name):
                    response = requests.get(plus_link, headers=headers)
                    source = response.content
                    phone_numbers = re.findall('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',source)
                    if phone_numbers: 
                        print uu(q)
                        profile.phone = phone_numbers[0]
                        session.add(profile)
                        session.commit()                            
                        return profile.phone
    if website:
        clearbit_response = clearbit.Company.find(domain=website)
        if clearbit_response and clearbit_response.get("phone"): 
            profile.phone = clearbit_response.get("phone")
            session.add(profile)
            session.commit()                            
            return profile.phone
    if profile.prospect:
        pipl_json = profile.prospect.get_pipl_contact_response
        if pipl_json: 
            pipl_valid_recs = []
            for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
                if not record.get('@query_params_match',True): continue
                pipl_valid_recs.append(record)
            pipl_json_str = json.dumps(pipl_valid_recs)
            if re.search('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',pipl_json_str):
                profile.phone = re.search('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',pipl_json_str).group(0)
                session.add(profile)
                session.commit()
                return profile.phone
    return profile.phone