import re
import logging
from difflib import SequenceMatcher
from constants import profile_re, bloomberg_company_re, school_re, company_re, SOCIAL_DOMAINS, BROWSERSTACK_USERNAME, BROWSERSTACK_KEY, LINKEDIN_EXPORT_URL
from helpers.stringhelpers import uu, get_domain, domain_match, name_match, get_firstname, resolve_email
from helpers.datehelpers import parse_date, date_overlap
from helpers.data_helpers import flatten, merge_by_key, most_common, parse_out, get_center
from helpers.linkedin_helpers import common_institutions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from itertools import izip, cycle
from captcha_solver import CaptchaSolver

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

def xor_crypt_string(plaintext, key):
    ciphertext = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(plaintext, cycle(key)))
    return ciphertext.encode('hex')

def xor_decrypt_string(ciphertext, key):
    ciphertext = ciphertext.decode('hex')
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(ciphertext, cycle(key)))

def get_remote_driver():
    desired_cap = {'browser': 'Firefox'}
    driver = webdriver.Remote(
    command_executor='http://{}:{}@hub.browserstack.com:80/wd/hub'.format(BROWSERSTACK_USERNAME, BROWSERSTACK_KEY),
    desired_capabilities=desired_cap)
    #driver.set_window_size(150, 80)
    return driver

def check_linkedin_creds(username, password):
    driver = get_remote_driver()
    driver.get("https://www.linkedin.com")
    email_el = driver.find_element_by_id("login-email")
    pw_el = driver.find_element_by_id("login-password")
    email_el.send_keys(username)
    pw_el.send_keys(password)
    button = driver.find_element_by_name("submit")
    button.click()
    if driver.title == u'Welcome! | LinkedIn':
        return driver
    return None

def get_linkedin_csv_captcha(driver):
    driver.get(LINKEDIN_EXPORT_URL)
    driver.save_screenshot("screenshot.png")
    solver = CaptchaSolver('browser')
    with open('screenshot.png', 'rb') as inp:
        raw_data = inp.read()
    captcha = solver.solve_captcha(raw_data)
    captcha_input = driver.find_element_by_id("recaptcha_response_field")
    captcha_input.send_keys(captcha)
    export_button = driver.find_element_by_name("exportNetwork")
    export_button.click()
    cookies = driver.get_cookies()
    return cookies
    # cookies_dict = {}
    # for cookie in cookies:
    #     cookies_dict[cookie.get("name")] = cookie.get("value")    
    # return cookies_dict
