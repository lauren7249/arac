import json
import urlparse
import lxml.html

import logging

def lxml_parse_html(html):
    html_el = lxml.html.fromstring(html)
  
    for div in html_el.xpath("div"):
        print div, div.text, div.items(), dir(div)

    for link in html_el.iterlinks():
        print link
