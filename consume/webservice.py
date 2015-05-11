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
import tinys3, os, pickle, boto
from boto.s3.key import Key

urls = (
    '/validate/username=(.+)&password=(.+)', 'validate',
    '/connections/username=(.+)', 'get_connections'
)

bucket_name='li-cookies'

global driver
global conn

def get_tinys3_conn():
    return tinys3.Connection(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"), tls=True, default_bucket=bucket_name)

def get_cookies_bucket():
    s3conn = boto.connect_s3(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"))
    return s3conn.get_bucket(bucket_name)

display = Display(visible=0, size=(1024, 768))
display.start()
#time.sleep(1)
profile=webdriver.FirefoxProfile()
profile.set_preference('permissions.default.stylesheet', 2)
## Disable images
profile.set_preference('permissions.default.image', 2)
## Disable Flash
profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')   
# import pdb 
# pdb.set_trace()  

driver = webdriver.Firefox(profile) 
conn = get_tinys3_conn()
bucket = get_cookies_bucket()

print driver.title

class get_connections:
    def GET(self, username):
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')    
        #driver.get("http://linkedin.com")
        key = Key(bucket)
        key.key = username
        cookies = pickle.loads(key.get_contents_as_string())
        for cookie in cookies:
            yield cookie.getValue()  

class validate:
    def GET(self, username, password):
        driver.get("http://linkedin.com")
        username_f = driver.find_element_by_name("session_key")
        password_f = driver.find_element_by_name("session_password")
        username_f.send_keys(username)
        password_f.send_keys(password)
        submit = driver.find_element_by_name("signin")
        submit.click()
        try:
            link = driver.find_elements_by_class_name("account-toggle")[0].get_attribute("href")
            linkedin_id  = link.split("&")[0].split("=")[1]
        except:
            return 'Invalid credentials'
        f = open(username,"wb")
        pickle.dump(driver.get_cookies(), f)
        f.close()
        f = open(username,'rb')
        conn.upload(username,f)
        os.remove(username)
        driver.delete_all_cookies()
        return linkedin_id      

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

