import random
import getpass
import argparse
import datetime
import time
import lxml.html
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pyvirtualdisplay import Display
from boto.s3.key import Key

class FacebookFriend(object):

    def __init__(self, *args, **kwargs):
        self.is_logged_in = False
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.completed = 0
        self.failed = 0
        self.prospects_completed = 0
        self.start_time = None
        self.successful_prospects = []
        self.linkedin_id = None
        self.test = kwargs.get("test")

    def login(self):
        # self.display = Display(visible=0, size=(1024, 768))
        # self.display.start()
        profile=webdriver.FirefoxProfile('/Users/lauren/Library/Application Support/Firefox/Profiles/lh4ow5q9.default')
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                      'false')
        profile.set_preference('permissions.default.image', 2)
        self.driver = webdriver.Firefox(profile)
        self.driver.implicitly_wait(3) 
        self.driver.set_page_load_timeout(5)
        self.wait = WebDriverWait(self.driver, 3)
        try:
            self.driver.get("http://www.facebook.com")
        except:
            self.driver.get("http://www.facebook.com")      
        try:
            self.wait.until(lambda driver: driver.find_elements_by_id("navPrivacy"))
        except:  
            try:      
                username = self.driver.find_element_by_name("email")
                password = self.driver.find_element_by_name("pass")
                #username.send_keys(self.username)
                password.send_keys(self.password)
                submit = self.driver.find_element_by_id("u_0_n")
                submit.click()
                self.wait.until(lambda driver: driver.find_elements_by_id("navPrivacy"))
            except:
                print "Error"
                return False
        self.is_logged_in = True
        return True


    def robust_scroll_to_bottom(self, xpath, break_at_xpath=None):
        current_count = self.scroll_to_bottom(xpath)
        if break_at_xpath and len(self.driver.find_elements_by_xpath(break_at_xpath)): return current_count
        while current_count != self.scroll_to_bottom(xpath):
            if break_at_xpath and len(self.driver.find_elements_by_xpath(break_at_xpath)): return current_count
            current_count = self.scroll_to_bottom(xpath)   
            if break_at_xpath and len(self.driver.find_elements_by_xpath(break_at_xpath)): return current_count
        return current_count

    def get_second_degree_connections(self, link):
        if not self.is_logged_in:
            self.login()        
        try:
            self.driver.get("https://www.facebook.com/" + link)
        except:
            self.driver.get("https://www.facebook.com/" + link)
        xpath=".//*[@class='uiProfileBlockContent']"
        current_count = self.robust_scroll_to_bottom(xpath)
        source = self.driver.page_source
        return self.parse_facebook_friends(source)

    def scroll_to_bottom(self, xpath):
        more_results = True
        current_count = 0
        #keep scrolling until you have all the contacts
        while more_results:
            try:
                self.wait.until(lambda driver:
                        driver.find_elements_by_xpath(xpath))
                current_count = len(self.driver.find_elements_by_xpath(xpath))    
                self.wait.until(lambda driver:
                        driver.find_elements_by_xpath(xpath)[-1]\
                                .location_once_scrolled_into_view)
                self.driver.find_elements_by_xpath(xpath)[-1]\
                                .location_once_scrolled_into_view
                more_results = self.wait.until(lambda driver: current_count <
                        len(driver.find_elements_by_xpath(xpath)))
                if current_count == previous_count:
                    more_results = False
                    break
                else:
                    more_results = True
            except Exception, e:
                break
            print current_count
            previous_count = current_count
        return current_count

    
    def shutdown(self):
        self.display.popen.terminate()
        self.driver.quit()
        return True


    def parse_facebook_friends(source):
        raw_html = lxml.html.fromstring(source)
        all_elements = raw_html.xpath("//div/div/div/div/div/div/ul/li/div")
        friends = []
        for person in all_elements:
            try:
                profile = person.xpath(".//*[@class='uiProfileBlockContent']")
                if len(profile) ==0: continue
                href = profile[0].find(".//a").get("href")
                username = href_to_username(href)
                friends.append(username)
            except Exception,e:
                username = None
                print e
                continue        
        return friends