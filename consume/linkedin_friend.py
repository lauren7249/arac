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


class LinkedinFriend(object):

    def __init__(self, *args, **kwargs):
        self.display = Display(visible=0, size=(1024, 768))
        self.display.start()
        time.sleep(2)
        self.driver = webdriver.Firefox()
        self.is_logged_in = False
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.completed = 0
        self.failed = 0
        self.prospects_completed = 0
        self.start_time = None
        self.successful_prospects = []
        self.linkedin_id = None
        self.wait = WebDriverWait(self.driver, 5)

    def login(self):
        self.driver.get("http://linkedin.com")
        username = self.driver.find_element_by_name("session_key")
        password = self.driver.find_element_by_name("session_password")
        username.send_keys(self.username)
        password.send_keys(self.password)
        submit = self.driver.find_element_by_name("signin")
        submit.click()
        self.wait.until(lambda driver: driver.find_elements_by_class_name("account-toggle"))
        link = self.driver.find_elements_by_class_name("account-toggle")[0].get_attribute("href")
        self.linkedin_id = self.get_linkedin_id(link)

        self.is_logged_in = True
        print self.linkedin_id
        return True

    def get_linkedin_id(self, link):
        clean_link  = link.split("&")[0].split("=")[1]
        if "li_" in clean_link:
            return clean_link.split("_")[1]
        self.driver.get(link.split("&")[0])
        return self.driver.current_url.split("=")[-1]

    def get_first_degree_connections(self):
        if not self.is_logged_in:
            self.login()
        first_degree_connections = []
        self.wait.until(lambda driver: driver.find_element_by_link_text("Connections"))
        self.driver.find_element_by_link_text("Connections").click()
        more_results = True
        current_count = 0
        #keep scrolling until you have all the contacts
        while more_results:
            try:
                self.wait.until(lambda driver:
                        driver.find_elements_by_class_name("contact-item-view"))
                self.wait.until(lambda driver:
                        driver.find_elements_by_class_name("contact-item-view")[-1]\
                                .location_once_scrolled_into_view)
                self.driver.find_elements_by_class_name("contact-item-view")[-1]\
                                .location_once_scrolled_into_view
                more_results = self.wait.until(lambda driver: current_count <
                        len(driver.find_elements_by_class_name("contact-item-view")))
                if current_count == len(self.driver.find_elements_by_class_name("contact-item-view")):
                    more_results = False
                    break
            except:
                more_results = False
                break
            current_count = len(self.driver.find_elements_by_class_name("contact-item-view"))
            print current_count

        people = self.driver.find_elements_by_class_name("contact-item-view")
        all_friend_links = []

        for person in people:
            element = person.find_element_by_class_name("image")
            link = element.get_attribute("href")
            all_friend_links.append(link)

        for friend_link in all_friend_links:
            linkedin_id = self.get_linkedin_id(friend_link)
            first_degree_connections.append(linkedin_id)
        print first_degree_connections
        return first_degree_connections

    def get_second_degree_connections(self, linkedin_id):
        self.driver.get("https://www.linkedin.com/profile/view?trk=contacts-contacts-list-contact_name-0&id=" + linkedin_id)
        try:
            element = self.wait.until(lambda driver: driver.find_element_by_class_name('connections-link'))
            element.click  
        except:
            return

        all_friend_ids = []
        while True:  
            import pdb 
            pdb.set_trace()
            self.wait.until(lambda driver: driver.find_element_by_class_name('connections-photo'))    

            all_friend_ids = findConnections(all_friend_ids)
            self.wait.until(lambda driver: driver.find_element_by_class_name('connections-paginate'))   
            
            connections_view = self.driver.find_element_by_class_name('connections-paginate')
            buttons = connections_view.find_elements_by_tag_name('button')
            try:
                next_button = buttons[1]
                next_button.click       
            except:
                break
        return all_friend_ids

    def findConnections(all_friend_ids):
        all_views = self.driver.find_elements_by_class_name("connections-photo")
        for view in all_views:
            try:
                link = view.get_attribute("href")
                linkedin_id =get_linkedin_id(link)
            except:
                try:
                    oops_link = self.driver.find_element_by_class_name("error-search-retry")
                    oops_link.click
                    self.wait.until(lambda driver: driver.find_elements_by_class_name('connections-photo'))
                    all_friend_ids = findConnections(all_friend_ids)                
                except:
                    all_friend_ids = findConnections(all_friend_ids)
            all_friend_ids.append(linkedin_id)
        return all_friend_ids

def run(username, password):
    ig = LinkedinFriend(
            username=username,
            password=password)
    ig.get_first_degree_connections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args()
    run(args.username, args.password)


