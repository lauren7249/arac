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
from prime.prospects.models import session, FacebookUrl, FacebookContact
from prime.utils import get_bucket
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
        self.bucket = get_bucket('facebook-profiles')

    def login(self):
        self.display = Display(visible=0, size=(1024, 768))
        self.display.start()
        profile=webdriver.FirefoxProfile('/Users/lauren/Library/Application Support/Firefox/Profiles/lh4ow5q9.default')
        self.driver = webdriver.Firefox(profile)
        self.driver.implicitly_wait(4) 
        self.wait = WebDriverWait(self.driver, 3)
        self.driver.get("http://www.facebook.com")
        try:
            self.wait.until(lambda driver: driver.find_elements_by_id("navPrivacy"))
        except:  
            try:      
                username = self.driver.find_element_by_name("email")
                password = self.driver.find_element_by_name("pass")
                username.send_keys(self.username)
                password.send_keys(self.password)
                submit = self.driver.find_element_by_id("u_0_x")
                submit.click()
                self.wait.until(lambda driver: driver.find_elements_by_id("navPrivacy"))
            except:
                return False
        self.is_logged_in = True
        return True

    def scrape_profile(self, link):
        xwalk = session.query(FacebookUrl).get(link)
        key = Key(self.bucket)
        if xwalk: 
            key.key = xwalk.username
        else:
            key.key = link.split("/")[-1]
        if key.exists(): return key.key
        if not self.is_logged_in:
            self.login()
        self.driver.get(link)
        real_url = self.driver.current_url
        username = real_url.split("/")[-1] if real_url[-1] != '/' else real_url.split("/")[-2] 
        if username.find("=") > -1: username = username.split("=")[-1]
        source = self.driver.page_source
        key.key = username
        key.content_type = 'text/html'
        key.set_contents_from_string(source)
        contact = session.query(FacebookContact).get(username)
        if not contact: 
            contact = FacebookContact(facebook_id=username)
            session.add(contact)
            session.commit()
        if not xwalk and link != real_url: 
            xwalk = FacebookUrl(url=link, username=username)
            session.add(xwalk)
            session.commit()
        return key.key

    def scrape_profile_friends(self, username):
        key = Key(self.bucket)
        key.key = username + "-friends"
        if key.exists(): return         
        if not self.is_logged_in:
            self.login()        
        self.driver.get("https://www.facebook.com/" + username + "/friends") 
        
        class_name="uiProfileBlockContent"
        current_count = self.scroll_to_bottom(class_name)
        while current_count != self.scroll_to_bottom(class_name):
            current_count = self.scroll_to_bottom(class_name)
        source = self.driver.page_source
        key.content_type = 'text/html'
        key.set_contents_from_string(source)

    def get_second_degree_connections(self, link):
        if not self.is_logged_in:
            self.login()        
        self.driver.get("https://www.facebook.com/" + link)
        
        class_name="uiProfileBlockContent"
        current_count = self.scroll_to_bottom(class_name)
        while current_count != self.scroll_to_bottom(class_name):
            current_count = self.scroll_to_bottom(class_name)

        self.all_friend_ids = []
        all_elements = self.driver.find_elements_by_xpath("//div/div/div/div/div/div/ul/li/div")
        people = {}
        for person in all_elements:
            uiProfileBlockContent = person.find_elements_by_class_name(class_name)
            if len(uiProfileBlockContent) ==0: continue
            image_url = person.find_element_by_tag_name("img").get_attribute("src")
            texts = uiProfileBlockContent[0].text.split("\n")
            name = texts[0]
            role = texts[1] if len(texts)>1 else None
            try:
                href = uiProfileBlockContent[0].find_element_by_tag_name("a").get_attribute("href")
                username = href.split("/")[-1].split("?")[0]
                if username == "profile.php":
                    username = href.split("/")[-1].split("?")[1].split("=")[1].split("&")[0]
            except:
                username = None
                continue
            d = {"name": name, "role": role, "image_url":image_url}
            people.update({username: d})
        return people

    def scroll_to_bottom(self, class_name):
        more_results = True
        current_count = 0
        #keep scrolling until you have all the contacts
        while more_results:
            try:
                self.wait.until(lambda driver:
                        driver.find_elements_by_class_name(class_name))
                current_count = len(self.driver.find_elements_by_class_name(class_name))    
                self.wait.until(lambda driver:
                        driver.find_elements_by_class_name(class_name)[-1]\
                                .location_once_scrolled_into_view)
                self.driver.find_elements_by_class_name(class_name)[-1]\
                                .location_once_scrolled_into_view
                more_results = self.wait.until(lambda driver: current_count <
                        len(driver.find_elements_by_class_name(class_name)))
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



