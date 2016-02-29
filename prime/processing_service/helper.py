import re
import logging
from difflib import SequenceMatcher
from constants import profile_re, bloomberg_company_re, school_re, company_re, SOCIAL_DOMAINS
from helpers.stringhelpers import uu, get_domain, domain_match, name_match, get_firstname, resolve_email, xor_crypt_string, xor_decrypt_string, random_string, csv_line_to_list
from helpers.datehelpers import parse_date, date_overlap
from helpers.data_helpers import flatten, merge_by_key, most_common, parse_out, get_center
from helpers.linkedin_helpers import common_institutions, process_csv

logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_bing_results(results, limit=100, url_regex=".", exclude_terms_from_title=None, include_terms_in_title=None):
    """
    Given a list of bing results, it will filter the results based on a url regex
    """
    filtered = []
    if exclude_terms_from_title: exclude_terms_from_title = re.sub("[^a-z\s]",'',exclude_terms_from_title.lower().strip())
    if include_terms_in_title: include_terms_in_title = re.sub("[^a-z\s]",'',include_terms_in_title.lower().strip())
    for result in results:
        link = result.get("Url")
        if re.search(url_regex,link, re.IGNORECASE):
            title = result.get("Title")
            title_meat = re.sub("[^a-z\s]",'',title.split("|")[0].lower().strip())
            if exclude_terms_from_title:
                ratio = SequenceMatcher(None, title_meat, exclude_terms_from_title.lower().strip()).ratio()
                intersect = set(exclude_terms_from_title.split(" ")) & set(title_meat.split(" "))
                if len(intersect) >= min(2,len(exclude_terms_from_title.split(" "))) or ratio>=0.8:
                    continue
            if include_terms_in_title:
                ratio = SequenceMatcher(None, title_meat, include_terms_in_title.lower().strip()).ratio()
                intersect = set(include_terms_in_title.split(" ")) & set(title_meat.split(" "))
                if len(intersect) < min(2,len(include_terms_in_title.split(" "))) and ratio<0.8:
                    continue
            filtered.append(link)
        if limit == len(filtered): return filtered
    return filtered

def get_specific_url(social_accounts, type="linkedin.com"):
    for account in social_accounts:
        if account.find(type) > -1: return account
    return None

def sort_social_accounts(social_accounts):
    d = {}
    for link in social_accounts:
        domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0].lower()
        if domain in SOCIAL_DOMAINS:
            d[domain] = link
    return d




