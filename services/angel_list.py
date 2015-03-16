import requests

angel_pages = {}

BASE_GOOGLE = "https://www.google.com/search?q=site:angel.co%20Investors&start={}"

for i in range(100):
    content = requests.get(BASE_GOOGLE.format(i*10))
    import pdb
    pdb.set_trace()
