import re
import logging
from difflib import SequenceMatcher
from constants import profile_re, bloomberg_company_re, school_re, company_re, SOCIAL_DOMAINS, BROWSERSTACK_USERNAME, BROWSERSTACK_KEY, LINKEDIN_EXPORT_URL, LINKEDIN_DOWNLOAD_URL, ANTIGATE_ACCESS_KEY, LINKEDIN_CAPTCHA_CROP_DIMS
from helpers.stringhelpers import uu, get_domain, domain_match, name_match, get_firstname, resolve_email
from helpers.datehelpers import parse_date, date_overlap
from helpers.data_helpers import flatten, merge_by_key, most_common, parse_out, get_center
from helpers.linkedin_helpers import common_institutions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from itertools import izip, cycle
#https://github.com/lorien/captcha_solver
from captcha_solver import CaptchaSolver
import requests
from PIL import Image
from random import choice
from string import ascii_uppercase
import shlex
from pyvirtualdisplay import Display
import os

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

def get_local_driver():
    display = Display(visible=0, size=(1024,1024))
    display.start()
    driver = webdriver.Firefox()
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

def random_string(length=12):
    return ''.join(choice(ascii_uppercase) for i in range(length))

def csv_line_to_list(line):
    splitter = shlex.shlex(line, posix=True)
    splitter.whitespace = ","
    splitter.whitespace_split=True
    return list(splitter)

def get_linkedin_data(driver):
    screenshot_fn = random_string() + ".png"
    cropped_fn = random_string()  + ".png"
    driver.get(LINKEDIN_EXPORT_URL)
    driver.save_screenshot(screenshot_fn)
    img = Image.open(screenshot_fn)
    img_cropped = img.crop( LINKEDIN_CAPTCHA_CROP_DIMS )
    imagefile = open(cropped_fn, 'wb')
    img_cropped.save(imagefile,"png",quality=100, **img.info)
    img_cropped.close()
    solver = CaptchaSolver('antigate', api_key=ANTIGATE_ACCESS_KEY)
    with open(cropped_fn, 'rb') as inp:
        raw_data = inp.read()
    captcha = solver.solve_captcha(raw_data)
    captcha_input = driver.find_element_by_id("recaptcha_response_field")
    captcha_input.send_keys(captcha)
    export_button = driver.find_element_by_name("exportNetwork")
    export_button.click()
    os.remove(cropped_fn)
    os.remove(screenshot_fn)
    cookies = driver.get_cookies()
    req_cookies = {}
    for cookie in cookies:
        req_cookies[cookie["name"]] = cookie["value"]
    response = requests.get(LINKEDIN_DOWNLOAD_URL, cookies=req_cookies)
    csv = response.content
    lines = csv.splitlines()
    if len(lines)<2:
        return None
    header = lines[0]
    cols = csv_line_to_list(header)
    first_name_index = cols.index('First Name')
    last_name_index = cols.index('Last Name')
    company_index = cols.index('Company')
    job_title_index = cols.index('Job Title')
    email_index = cols.index('E-mail Address')
    if min(first_name_index, last_name_index, company_index, job_title_index, email_index) < 0:
        return None
    data = []
    for i in xrange(1, len(lines)):
        line = csv_line_to_list(lines[i])
        if len(line) <= max(first_name_index, last_name_index, company_index, job_title_index, email_index):
            logger.warn("Linkedin csv line is wrong:\r\n{}".format(lines[i]))
            continue
        contact = {}
        contact["first_name"] = line[first_name_index].decode('latin-1')
        contact["last_name"] = line[last_name_index].decode('latin-1')
        contact["companies"] = [line[company_index].decode('latin-1')]
        contact["email"] = [{"address": line[email_index].decode('latin-1')}]
        contact["job_title"] = line[job_title_index].decode('latin-1')
        data.append({"contact":contact, "contacts_owner":None, "service":"LinkedIn"})        
    return data

