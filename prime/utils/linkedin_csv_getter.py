from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium import webdriver
from prime.processing_service.constants import LINKEDIN_EXPORT_URL, LINKEDIN_DOWNLOAD_URL, ANTIGATE_ACCESS_KEY, LINKEDIN_CAPTCHA_CROP_DIMS, SAUCE_USERNAME, SAUCE_ACCESS_KEY, LINKEDIN_YAHOO_DOWNLOAD_URL
from pyvirtualdisplay import Display
#https://github.com/lorien/captcha_solver
from captcha_solver import CaptchaSolver
import requests
from PIL import Image
from prime.processing_service.helper import  random_string, process_csv
import os
import signal
import subprocess
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import Select
import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

class LinkedinCsvGetter(object):

    def __getstate__(self):
        d = self.__dict__.copy()
        if 'logger' in d.keys():
            d['logger'] = d['logger'].name
        return d

    def __setstate__(self, d):
        if 'logger' in d.keys():
            d['logger'] = logging.getLogger(d['logger'])
        self.__dict__.update(d)

    def __init__(self, username, password, local=True):
        self.username = username
        self.password = password
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.display = None
        self.via_google = True
        if local:
            self.driver = self.get_local_driver()
        else:
            self.driver = self.get_remote_driver()
        if self.via_google:
            self.desired_title = "My Contacts: Export LinkedIn Connections | LinkedIn"
        else:
            self.desired_title = 'Welcome! | LinkedIn'

    def kill_firefox_and_xvfb(self):
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        for i, line in enumerate(out.splitlines()):
            if i > 0:
                if 'firefox' in line or 'xvfb' in line.lower():
                    print line
                    pid = int(line.split(None, 1)[0])
                    os.kill(pid, signal.SIGKILL)
                    print "killed"

    def quit(self):
        if self.driver:
            self.driver.quit()
        if self.display:
            self.display.sendstop()
        self.kill_firefox_and_xvfb()

    def give_pin(self, pin):
        self.logger.info("Pin Started: {}".format(pin))
        pin_form = self.driver.find_element_by_id("verification-code")
        pin_form.clear()
        pin_form.send_keys(pin)
        time.sleep(4)
        self.driver.save_screenshot("pin_typed.png")
        button = self.driver.find_element_by_xpath("//input[@type='submit']")
        button.click()
        time.sleep(5)
        self.logger.info("Pin Submitted Title: {}".format(self.driver.title))
        self.driver.save_screenshot("pin_submitted.png")
        if self.driver.title == self.desired_title:
            self.logger.info("Pin Success")
            return True
        self.logger.info("Pin Failure")
        return False

    def get_remote_driver(self, proxy=False):

        if proxy:
            PROXY = "https://pp-suibscag:eenamuts@66.90.79.52:11332"

            proxy = Proxy({
                'proxyType': ProxyType.MANUAL,
                'httpProxy': PROXY,
                'ftpProxy': PROXY,
                'sslProxy': PROXY,
                'noProxy': '' # set this value as desired
                })

            driver = webdriver.Firefox(proxy=proxy)
            desired_capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
            proxy.add_to_capabilities(desired_capabilities)
            driver.quit()
        else:
            desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
        self.driver = webdriver.Remote(desired_capabilities=desired_capabilities,command_executor='http://%s:%s@ondemand.saucelabs.com:80/wd/hub' %(SAUCE_USERNAME, SAUCE_ACCESS_KEY))
        return self.driver

    def get_local_driver(self):
        self.display = Display(visible=0, size=(1024,1024))
        self.display.start()
        self.driver = webdriver.Firefox()
        return self.driver

    def get_request_cookies(self):
        cookies = self.driver.get_cookies()
        self.req_cookies = {}
        for cookie in cookies:
            self.req_cookies[cookie["name"]] = cookie["value"]
        return self.req_cookies

    def do_captcha(self):
        self.logger.info("Linkedin Export URL: {}".format(self.driver.title))
        try:
            captcha_input = self.driver.find_element_by_id("recaptcha_response_field")
            captcha_exists = True
        except:
            captcha_exists = False
        if captcha_exists:
            screenshot_fn = random_string() + ".png"
            cropped_fn = random_string()  + ".png"
            self.driver.save_screenshot(screenshot_fn)
            img = Image.open(screenshot_fn)
            img_cropped = img.crop( LINKEDIN_CAPTCHA_CROP_DIMS )
            imagefile = open(cropped_fn, 'wb')
            img_cropped.save(imagefile,"png",quality=100, **img.info)
            img_cropped.close()
            solver = CaptchaSolver('antigate', api_key=ANTIGATE_ACCESS_KEY)
            with open(cropped_fn, 'rb') as inp:
                raw_data = inp.read()
            os.remove(cropped_fn)
            os.remove(screenshot_fn)
            try:
                captcha = solver.solve_captcha(raw_data)
                captcha_input.send_keys(captcha)
            except Exception, e:
                print str(e)
                self.driver.save_screenshot("error.png")
                return False
        return True

    def check_linkedin_login_errors(self):
        if self.via_google:
            return self.check_creds_via_google()
        self.driver.get("https://www.linkedin.com")
        email_el = self.driver.find_element_by_id("login-email")
        pw_el = self.driver.find_element_by_id("login-password")
        email_el.send_keys(self.username)
        pw_el.send_keys(self.password)
        button = self.driver.find_element_by_name("submit")
        button.click()
        if self.driver.title == self.desired_title:
            return None, None
        if self.driver.current_url=='https://www.linkedin.com/uas/consumer-email-challenge':
            self.driver.save_screenshot("challenge.png")
            cookies = self.driver.get_cookies()
            req_cookies = {}
            for cookie in cookies:
                req_cookies[cookie["name"]] = cookie["value"]
            try:
                message = self.driver.find_element_by_class_name("descriptor-text")
            except:
                message = self.driver.find_element_by_id("verification-code")
            if message:
                return message.text.split(". ")[-1], req_cookies
            return "Please enter the verification code sent to your email address to finish signing in.", req_cookies
        email_error = self.driver.find_element_by_id("session_key-login-error")
        if email_error and email_error.text:
            self.driver.save_screenshot("email_error.png")
            return email_error.text, None
        pw_error = self.driver.find_element_by_id("session_password-login-error")
        if pw_error and pw_error.text:
            self.driver.save_screenshot("pw_error.png")
            return pw_error.text, None
        self.driver.save_screenshot("Unknown_error.png")
        return "Unknown error", None

    def check_creds_via_google(self):
        self.driver.get("https://www.linkedin.com/uas/login?session_redirect=https%3A%2F%2Fwww%2Elinkedin%2Ecom%2Fpeople%2Fexport-settings&fromSignIn=true&trk=uno-reg-join-sign-in")
        time.sleep(4)
        email_el = self.driver.find_element_by_id("session_key-login")
        pw_el = self.driver.find_element_by_id("session_password-login")
        email_el.send_keys(self.username)
        pw_el.send_keys(self.password)
        button = self.driver.find_element_by_id("btn-primary")
        button.click()
        time.sleep(3)
        if self.driver.current_url == 'https://www.linkedin.com/people/export-settings':
            return None, None
        if self.driver.current_url=='https://www.linkedin.com/uas/consumer-email-challenge':
            self.driver.save_screenshot("challenge.png")
            cookies = self.driver.get_cookies()
            req_cookies = {}
            for cookie in cookies:
                req_cookies[cookie["name"]] = cookie["value"]
            try:
                message = self.driver.find_element_by_class_name("descriptor-text")
            except:
                message = self.driver.find_element_by_id("verification-code")
            if message:
                return message.text.split(". ")[-1], req_cookies
            return "Please enter the verification code sent to your email address to finish signing in.", req_cookies
        try:
            change_password = self.driver.find_element_by_id("li-dialog-aria-label")
            self.driver.get("https://www.linkedin.com/people/export-settings")
            if self.driver.current_url == 'https://www.linkedin.com/people/export-settings':
                return None, None
            if self.driver.current_url=='https://www.linkedin.com/uas/consumer-email-challenge':
                self.driver.save_screenshot("challenge.png")
                cookies = self.driver.get_cookies()
                req_cookies = {}
                for cookie in cookies:
                    req_cookies[cookie["name"]] = cookie["value"]
                try:
                    message = self.driver.find_element_by_class_name("descriptor-text")
                except:
                    message = self.driver.find_element_by_id("verification-code")
                if message:
                    return message.text.split(". ")[-1], req_cookies
                return "Please enter the verification code sent to your email address to finish signing in.", req_cookies
        except:
            pass
        try:
            email_error = self.driver.find_element_by_id("session_key-login-error")
            if email_error and email_error.text:
                self.driver.save_screenshot("email_error.png")
                return email_error.text, None
            pw_error = self.driver.find_element_by_id("session_password-login-error")
            if pw_error and pw_error.text:
                self.driver.save_screenshot("pw_error.png")
                return pw_error.text, None
        except:
            pass
        self.driver.save_screenshot("Unknown_error.png")
        return "Unknown error", None

    def get_linkedin_data(self):
        if self.via_google:
            return self.get_linkedin_data_yahoo()
        self.driver.get(LINKEDIN_EXPORT_URL)
        captcha_solved = self.do_captcha()
        if not captcha_solved:
            return None
        export_button = self.driver.find_element_by_name("exportNetwork")
        export_button.click()
        self.req_cookies = self.get_request_cookies()
        response = requests.get(LINKEDIN_DOWNLOAD_URL, cookies=self.req_cookies)
        csv = response.content
        data = process_csv(csv)
        return data

    def get_linkedin_data_yahoo(self):
        try:
            select = Select(self.driver.find_element_by_id('outputType-exportSettingsForm'))
            select.select_by_visible_text('Yahoo! Mail (.CSV file)')
            button = self.driver.find_element_by_class_name("btn-primary")
            button.click()
        except:
            self.driver.save_screenshot("selecting_yahoo.png")
        captcha_solved = self.do_captcha()
        if not captcha_solved:
            return None
        button = self.driver.find_element_by_class_name("btn-primary")
        button.click()
        self.req_cookies = self.get_request_cookies()
        response = requests.get(LINKEDIN_YAHOO_DOWNLOAD_URL, cookies=self.req_cookies)
        csv = response.content
        data = process_csv(csv)
        return data
