from selenium import webdriver
from pyvirtualdisplay import Display

def create_browser(tor=False):
	display = Display(visible=0, size=(1024, 768))
	display.start()
	profile=webdriver.FirefoxProfile()
	if tor:
		profile.set_preference('network.proxy.type', 1)
		profile.set_preference('network.proxy.socks', '127.0.0.1')
		profile.set_preference('network.proxy.socks_port',9050)
	profile.set_preference("javascript.enabled", False)
	## Disable CSS
	profile.set_preference('permissions.default.stylesheet', 2)
	## Disable images
	profile.set_preference('permissions.default.image', 2)
	## Disable Flash
	profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')
	browser=webdriver.Firefox(profile)
	return browser

def get_url_to_file(url, browser): 
	browser.get(url)
	filename = 	url[len("https://www.linkedin.com/"):].replace("/","_")
	text_file = open(filename, "w")
	text_file.write(browser.page_source.encode("ascii", "ignore").decode("utf-8"))
	text_file.close()