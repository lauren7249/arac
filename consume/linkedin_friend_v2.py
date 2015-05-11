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
import tinys3, os, pickle

def get_tinys3_conn():
    return tinys3.Connection(os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"), tls=True, default_bucket='li-cookies')

def validate_linkedin(username, password):
	conn = get_tinys3_conn()
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
	#driver.implicitly_wait(10)
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
		return ''
	f = open(username,"wb")
	pickle.dump(driver.get_cookies(), f)
	f.close()
	f = open(username,'rb')
	conn.upload(username,f)
	os.remove(username)
	return linkedin_id 


def get_driver(username, password):
	try:
		cookies_file = conn.get(username)
		driver = restart_linkedin(cookies_file)
	except:
		driver = login_linkedin(username, password, conn)
		