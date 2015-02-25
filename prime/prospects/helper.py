import requests
import itertools
import urlparse
import urllib
import urllib2
import json

class BingSearch(object):

    def __init__(self, query, *args, **kwargs):
        self.query = urllib.quote(query)
        self.key = "Qk8G0Qg6Hq4TOCEhanrCrtol5cjw+9Ye0qrg+ls75oI"
        self.url = "https://api.datamarket.azure.com/Bing/Search/v1/Web?Query=%27" + self.query + "%27&$format=json"

    def _build_request(self):
        return requests.get(self.url, auth=(self.key, self.key))

    def search(self):
        response = self._build_request()
        json_result = json.loads(response.content)
        return json_result['d']['results']


class LinkedinResults(object):

    def __init__(self, query, *args, **kwargs):
        self.bing = BingSearch("%s site:linkedin.com" % query)

    def process(self):
        results = self.bing.search()
        profile_results = []
        for result in results:
            url = result.get("Url")
            title = result.get("Title").split("|")[0].capitalize()
            if "linkedin" in url:
                if not "dir" in url:
                    ref = {"url": url,
                            "title": title}
                    profile_results.append(ref)
        return profile_results[:8]

