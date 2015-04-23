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
        #self.display = Display(visible=0, size=(1024, 768))
        #self.display.start()
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
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        self.driver.get("http://linkedin.com")
        #WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.liSpinnerLayer")))
        #username = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
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

    def _print_time(self):
        current_time = datetime.timedelta(seconds=time.time() - \
                self.start_time)
        print "Time Elapsed: {0} {1}: liked {2}: failed\n".format(\
                    current_time,
                    self.completed,\
                    self.failed)

    def _get_media_id(self):
        user_media = self.driver.execute_script("return window._sharedData")
        return user_media.get('entry_data').get('UserProfile')[0]\
                .get('userMedia')[0].get('id')

    def get_first_d(self):
        liked_media = {}
        self.start_time = time.time()
        if not self.is_logged_in:
            self._login()
            time.sleep(10)
        for prospect in self.prospects:
            try:
                links = self._find_links(prospect)
                if len(links) > 1:
                    link = links[0]
                    link.click()
                    time.sleep(5)
                    element_to_like = self.driver.find_element_by_xpath("//a[contains(@class, 'LikeButton')]")
                    element_to_like.click()
                    time.sleep(2)
                    if "ButtonActive" in element_to_like.get_attribute("class"):
                        self.driver.find_element_by_xpath("//i[@class='igDialogClose']").click()
                        self.completed += 1
                        try:
                            media_id =self._get_media_id()
                        except:
                            media_id = None
                        print media_id
                        liked_media[prospect] = media_id
                        time.sleep(22)
                    else:
                        self.failed += 1
                        print "like failed"
                        time.sleep(60)
                    self._print_time()
            except Exception, e:
                self.failed += 1
                client.captureException()
                print e, prospect, prospect_id
        self.driver.quit()
        self.display.popen.kill()
        return liked_media

    def comment(self, text):
        self.start_time = time.time()
        if not self.is_logged_in:
            self._login()
            time.sleep(10)
        for prospect_id in self.prospects:
            prospect = session.query(ProspectProfile).get(prospect_id)
            prospect.done = True
            session.commit()
            links = self._find_links(prospect.prospect.username)
            if len(links) > 1:
                try:
                    link = links[0]
                    link.click()
                    time.sleep(5)
                    element_to_comment = self.driver.find_element_by_xpath("//input[@class='fbInput']")
                    element_to_comment.send_keys(text)
                    element_to_comment.send_keys(Keys.RETURN)
                    self._print_time()
                    self.completed += 1
                    self.successful_prospects.append(prospect)
                    time.sleep(15)
                except Exception, e:
                    self.failed += 1
                    client.captureException()
                    print e
        self.driver.quit()
        self.display.popen.kill()
        print self.successful_prospects, "old_insta 142"
        return self.successful_prospects

def run(username, password):
    ig = LinkedinFriend(
            username=username,
            password=password)
    ig.get_first_degree_connections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    password = getpass.getpass()
    run(args.username, password)


