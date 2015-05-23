from consume.proxy_scrape import queue_url

urls = "/Users/lauren/Downloads/li.urls"
infile = open(urls,"rb")
for url in infile:
    url = url.strip()
    if url.find("://www.linkedin.com/pub/") < 0:
        queue_url(url, queue_name="malformed_urls")
