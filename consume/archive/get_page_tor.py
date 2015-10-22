from selenium import webdriver
from pyvirtualdisplay import Display
import sys
url = sys.argv[1]
print url
display = Display(visible=0, size=(1024, 768))
display.start()
profile=webdriver.FirefoxProfile()
profile.set_preference('network.proxy.type', 1)
profile.set_preference('network.proxy.socks', '127.0.0.1')
profile.set_preference('network.proxy.socks_port',9050)
profile.set_preference("javascript.enabled", False)
browser=webdriver.Firefox(profile)
browser.get(url)
print browser.title