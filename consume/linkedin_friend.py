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
        self.display = Display(visible=0, size=(1024, 768))
        self.display.start()
        time.sleep(2)
        if self.test:
            profile=webdriver.FirefoxProfile()
            profile.set_preference('permissions.default.stylesheet', 2)
            ## Disable images
            profile.set_preference('permissions.default.image', 2)
            ## Disable Flash
            profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')
            #tor doesnt work
            # profile.set_preference('network.proxy.type', 1)
            # profile.set_preference('network.proxy.socks', '127.0.0.1')
            # profile.set_preference('network.proxy.socks_port',9050)
            #profile.set_preference("javascript.enabled", False)        
            self.driver = webdriver.Firefox(profile)
        else:
            self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 15)
        self.driver.get("http://linkedin.com")
        username = self.driver.find_element_by_name("session_key")
        password = self.driver.find_element_by_name("session_password")
        username.send_keys(self.username)
        password.send_keys(self.password)
        try:
            submit = self.driver.find_element_by_name("signin")
        except:
            submit = self.driver.find_element_by_name("submit")
        submit.click()
        try:
            self.wait.until(lambda driver: driver.find_elements_by_class_name("account-toggle"))
            link = self.driver.find_elements_by_class_name("account-toggle")[0].get_attribute("href")
            self.linkedin_id = self.get_linkedin_id(link, mine=True)
        except:
            return False
        self.is_logged_in = True
        print self.linkedin_id
        return True

    def get_linkedin_id(self, link, mine=False, second_degree=False):
        clean_link  = link.split("&")[0].split("=")[1]
        if mine: return clean_link
        if "li_" in clean_link or second_degree:
            if "li_" in clean_link: return clean_link.split("_")[1]
            return clean_link
        self.driver.get(link)
        print self.driver.current_url
        lid = self.driver.current_url[self.driver.current_url.index("id=")+3:]
        if "&" in lid: lid = lid.split("&")[0]
        return lid

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
            if self.test and current_count>10: break

        people = self.driver.find_elements_by_class_name("contact-item-view")
        all_friend_links = []

        for person in people:
            try:
                element = person.find_element_by_class_name("image")
                link = element.get_attribute("href")
                print link
                all_friend_links.append(link)
                if self.test and len(all_friend_links)>10: break
            except:
                continue

        for friend_link in all_friend_links:
            try:
                linkedin_id = self.get_linkedin_id(friend_link)
                #print linkedin_id
                first_degree_connections.append(linkedin_id)
            except:
                continue

        print first_degree_connections
        return first_degree_connections

    def get_second_degree_connections(self, linkedin_id):
        if not self.is_logged_in:
            self.login()        
        self.driver.get("https://www.linkedin.com/profile/view?trk=contacts-contacts-list-contact_name-0&id=" + linkedin_id)
        try:
            element = self.wait.until(lambda driver: driver.find_element_by_class_name('connections-link'))
            element.click()
        except:
            return

        self.all_friend_ids = []
        while True:  
            try:
                self.findConnections()
                self.wait.until(lambda driver: driver.find_element_by_class_name('connections-paginate'))   
                
                connections_view = self.driver.find_element_by_class_name('connections-paginate')
                buttons = connections_view.find_elements_by_tag_name('button')
            
                next_button = buttons[1]
                next_button.click()
            except Exception, e:
                print e
                break
        return self.all_friend_ids

    def findConnections(self):
        all_views = self.wait.until(lambda driver: driver.find_elements_by_class_name('connections-photo'))    
        for view in all_views:
            try:
                link = view.get_attribute("href")
                linkedin_id =self.get_linkedin_id(link, second_degree=True)
                self.all_friend_ids.append(linkedin_id)
                print linkedin_id
            except:
                try:
                    oops_link = self.driver.find_element_by_class_name("error-search-retry")
                    oops_link.click()
                    self.wait.until(lambda driver: driver.find_elements_by_class_name('connections-photo'))
                    self.findConnections()             
                except:
                    self.findConnections()
            
    
    def shutdown(self):
        self.display.popen.terminate()
        self.driver.quit()
        return True

def run(username, password):
    ig = LinkedinFriend(
            username=username,
            password=password)
    ig.get_first_degree_connections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("test")
    args = parser.parse_args()
    run(args.username, args.password, test=args.test)


