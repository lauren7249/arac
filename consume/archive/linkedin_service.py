import web
import random
import getpass
import argparse
import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pyvirtualdisplay import Display
import tinys3, os, pickle, boto, subprocess, shlex, sys, signal
from boto.s3.key import Key

web.config.debug = False
urls = (
    '/validate/username=(.+)&password=(.+)', 'validate',
    '/connections/username=(.+)&password=(.+)', 'get_connections'
)

print "starting webservice"
bucket_name='li-cookies'

global driver
global conn
global bucket

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

def get_linkedin_id(driver, link, mine=False, second_degree=False):
    clean_link  = link.split("&")[0].split("=")[1]
    if mine: return clean_link
    if "li_" in clean_link or second_degree:
        if "li_" in clean_link: return clean_link.split("_")[1]
        return clean_link
    driver.get(link)
    print driver.current_url
    lid = driver.current_url[driver.current_url.index("id=")+3:]
    if "&" in lid: lid = lid.split("&")[0]
    return lid


def get_tinys3_conn():
    return tinys3.Connection(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"), tls=True, default_bucket=bucket_name)

def get_cookies_bucket():
    s3conn = boto.connect_s3(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    return s3conn.get_bucket(bucket_name)

def kill_firefox_and_xvfb():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for i, line in enumerate(out.splitlines()):
        if i > 0:
            if 'firefox' in line or 'xvfb' in line.lower():
                print line
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)
                print "killed"

# def start_fastest_driver():
#   display = Display(visible=0, size=(1, 1))
#   display.start()
#   profile=webdriver.FirefoxProfile()
#   profile.set_preference('permissions.default.stylesheet', 2)
#   ## Disable images
#   profile.set_preference('permissions.default.image', 2)
#   ## Disable Flash
#   profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')   
#   #profile.set_preference('javascript.enabled', False)
#   return webdriver.Firefox(profile)   

# def login_from_cookie(driver, bucket, username):
#   key = Key(bucket)
#   key.key = username
#   cookies = pickle.loads(key.get_contents_as_string())
#   driver.get("http://linkedin.com")
#   for cookie in cookies:
#       if cookie['domain'] == ".linkedin.com":
#           print cookie
#           driver.add_cookie(cookie)
#   driver.get("http://www.linkedin.com")
#   for cookie in cookies:
#       if cookie['domain'] == "www.linkedin.com":
#           print cookie
#           driver.add_cookie(cookie)       

def start_login_driver():
    print "starting webdriver"
    display = Display(visible=0, size=(1024, 768))
    display.start()
    profile=webdriver.FirefoxProfile()
    profile.set_preference('permissions.default.stylesheet', 2)
    ## Disable images
    profile.set_preference('permissions.default.image', 2)
    ## Disable Flash
    profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')   
    return webdriver.Firefox(profile)   

def login(driver, username, password):
    driver.get("http://linkedin.com")
    username_f = driver.find_element_by_name("session_key")
    password_f = driver.find_element_by_name("session_password")
    username_f.send_keys(username)
    password_f.send_keys(password)
    submit = driver.find_element_by_name("signin")
    submit.click()  

kill_firefox_and_xvfb()

class get_connections:
    def GET(self, username, password):
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')    
        driver = start_login_driver()
        login(driver, username, password)
        #try:
        link = driver.find_elements_by_class_name("account-toggle")[0].get_attribute("href")
        linkedin_id  = link.split("&")[0].split("=")[1]
        wait = WebDriverWait(driver, 10)
        driver2 = start_login_driver()
        login(driver2, username, password)
        driver.find_element_by_link_text("Connections").click()
        more_results = True
        current_count = 0
        #keep scrolling until you have all the contacts
        finished_elements = set()
        while more_results:
            for person in driver.find_elements_by_class_name("contact-item-view"):
                if person not in finished_elements:        
                    element = person.find_element_by_class_name("image")
                    link = element.get_attribute("href")                                    
                    friend_linkedin_id = get_linkedin_id(driver2, link)
                    yield friend_linkedin_id + "\n"
                    finished_elements.add(person)
            #try:
            wait.until(lambda driver:
                    driver.find_elements_by_class_name("contact-item-view"))
            wait.until(lambda driver:
                    driver.find_elements_by_class_name("contact-item-view")[-1]\
                            .location_once_scrolled_into_view)
            driver.find_elements_by_class_name("contact-item-view")[-1]\
                            .location_once_scrolled_into_view
            more_results = wait.until(lambda driver: current_count <
                    len(driver.find_elements_by_class_name("contact-item-view")))

            if current_count == len(driver.find_elements_by_class_name("contact-item-view")):
                more_results = False
                break
            # except:
            #   print sys.exc_info()[0]
            #     more_results = False
            #     break
            current_count = len(driver.find_elements_by_class_name("contact-item-view"))            
        # except:
        #   kill_firefox_and_xvfb()
        driver.save_screenshot('screenshot.png')
        print "done"

class validate:
    def GET(self, username, password):
        driver = start_login_driver()
        login(driver, username, password)
        try:
            link = driver.find_elements_by_class_name("account-toggle")[0].get_attribute("href")
            linkedin_id  = link.split("&")[0].split("=")[1]
        except:
            kill_firefox_and_xvfb()
            return 'Invalid credentials'
        f = open(username,"wb")
        pickle.dump(driver.get_cookies(), f)
        f.close()
        f = open(username,'rb')
        conn.upload(username,f)
        os.remove(username)
        kill_firefox_and_xvfb()
        return linkedin_id      

if __name__ == "__main__":
    global driver
    global conn 
    global bucket
    conn = get_tinys3_conn()
    bucket = get_cookies_bucket()   
    app.run()

