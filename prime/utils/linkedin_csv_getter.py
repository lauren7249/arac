from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from prime.processing_service.constants import BROWSERSTACK_USERNAME, BROWSERSTACK_KEY, LINKEDIN_EXPORT_URL, LINKEDIN_DOWNLOAD_URL, ANTIGATE_ACCESS_KEY, LINKEDIN_CAPTCHA_CROP_DIMS, SAUCE_USERNAME, SAUCE_ACCESS_KEY
from pyvirtualdisplay import Display
#https://github.com/lorien/captcha_solver
from captcha_solver import CaptchaSolver
import requests
from PIL import Image
from prime.processing_service.helper import  random_string, csv_line_to_list
import os
import signal
import subprocess
from selenium.webdriver.common.keys import Keys
import time

class LinkedinCsvGetter(object):

    def __init__(self, username, password, local=True):
        self.username = username
        self.password = password
        self.display = None
        if local:
            self.driver = self.get_local_driver()
        else:
            self.driver = self.get_remote_driver()

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
        pin_form = self.driver.find_element_by_id("verification-code")
        pin_form.clear()
        pin_form.send_keys(pin)
        time.sleep(6)
        pin_form.send_keys(Keys.RETURN)
        time.sleep(6)
        if self.driver.title == u'Welcome! | LinkedIn':
            return True
        return False

    def get_remote_driver(self):
        # desired_cap = {'browser': 'Firefox'}
        # #driver = webdriver.Remote(command_executor='http://{}:{}@hub.browserstack.com:80/wd/hub'.format(BROWSERSTACK_USERNAME, BROWSERSTACK_KEY),desired_capabilities=desired_cap)
        # PROXY = "https://pp-suibscag:eenamuts@66.90.79.52:11332"

        # webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
        #     "httpProxy":PROXY,
        #     "ftpProxy":PROXY,
        #     "sslProxy":PROXY,
        #     "noProxy":None,
        #     "proxyType":"MANUAL",
        #     "class":"org.openqa.selenium.Proxy",
        #     "autodetect":False
        # }
        self.driver = webdriver.Remote(desired_capabilities=webdriver.DesiredCapabilities.FIREFOX,command_executor='http://%s:%s@ondemand.saucelabs.com:80/wd/hub' %(SAUCE_USERNAME, SAUCE_ACCESS_KEY))
        return self.driver

    def get_local_driver(self):
        self.display = Display(visible=0, size=(1024,1024))
        self.display.start()
        self.driver = webdriver.Firefox()
        return self.driver

    def check_linkedin_login_errors(self):
        self.driver.get("https://www.linkedin.com")
        email_el = self.driver.find_element_by_id("login-email")
        pw_el = self.driver.find_element_by_id("login-password")
        email_el.send_keys(self.username)
        pw_el.send_keys(self.password)
        button = self.driver.find_element_by_name("submit")
        button.click()
        if self.driver.title == u'Welcome! | LinkedIn':
            return None, None
        if self.driver.current_url=='https://www.linkedin.com/uas/consumer-email-challenge':
            self.driver.save_screenshot("challenge.png")
            cookies = self.driver.get_cookies()
            req_cookies = {}
            for cookie in cookies:
                req_cookies[cookie["name"]] = cookie["value"]
            message = self.driver.find_element_by_class_name("descriptor-text")
            if message:
                return message.text.split(". ")[-1], req_cookies
            return "Please enter the verification code sent to your email address to finish signing in.", req_cookies
        pw_error = self.driver.find_element_by_id("session_password-login-error")
        if pw_error:
            return pw_error.text, None
        email_error = self.driver.find_element_by_id("session_key-login-error")
        if email_error:
            return email_error.text, None
        return "Unknown error", None

    def get_linkedin_data(self):
        screenshot_fn = random_string() + ".png"
        cropped_fn = random_string()  + ".png"
        self.driver.get(LINKEDIN_EXPORT_URL)
        self.driver.save_screenshot(screenshot_fn)
        img = Image.open(screenshot_fn)
        img_cropped = img.crop( LINKEDIN_CAPTCHA_CROP_DIMS )
        imagefile = open(cropped_fn, 'wb')
        img_cropped.save(imagefile,"png",quality=100, **img.info)
        img_cropped.close()
        solver = CaptchaSolver('antigate', api_key=ANTIGATE_ACCESS_KEY)
        with open(cropped_fn, 'rb') as inp:
            raw_data = inp.read()
        try:
            captcha = solver.solve_captcha(raw_data)
            captcha_input = self.driver.find_element_by_id("recaptcha_response_field")
            captcha_input.send_keys(captcha)
            export_button = self.driver.find_element_by_name("exportNetwork")
            export_button.click()
        except Exception, e:
            print str(e)
            self.driver.save_screenshot("error.png")
            return None
        os.remove(cropped_fn)
        os.remove(screenshot_fn)
        cookies = self.driver.get_cookies()
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
