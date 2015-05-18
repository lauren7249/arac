from selenium import webdriver
from pyvirtualdisplay import Display
import time
import socket

socket.setdefaulttimeout(15)
def launch_browser(size=(1024, 768), tor=False, proxy=None, minimal=True):
    display = Display(visible=0, size=size)
    display.start()
    time.sleep(2)
    profile=webdriver.FirefoxProfile()
    ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    profile.set_preference("general.useragent.override",ua)

    if minimal:
        profile.set_preference("javascript.enabled", False)
        ## Disable CSS
        profile.set_preference('permissions.default.stylesheet', 2)
        ## Disable images
        profile.set_preference('permissions.default.image', 2)
        ## Disable Flash
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')

    #linkedin usually blocks tor with a security verification
    if tor:
        profile.set_preference('network.proxy.type', 1)
        profile.set_preference('network.proxy.socks', '127.0.0.1')
        profile.set_preference('network.proxy.socks_port',9050)

    elif proxy is not None:
        protocol = proxy.split(":")[0]
        proxy = proxy.split("/")[1]
        ip = proxy.split(":")[0]
        port = int(proxy.split(":")[1])     
        profile.set_preference('network.proxy.' + protocol, ip)
        profile.set_preference('network.proxy.' + protocol + '_port',port)

    browser=webdriver.Firefox(profile)
    return display, browser
