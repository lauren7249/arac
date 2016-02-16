import requests
import json
from random import shuffle

def get_proxy():
    response = requests.get("https://api.myprivateproxy.net/v1/fetchProxies/json/full/t2yb8f6r435698l6spp9guadphnne8nw")
    all_proxies = json.loads(response.content)
    shuffle(all_proxies)
    proxy =  all_proxies[0]
