#For Deduping real emails
EXCLUDED_EMAIL_WORDS = ["reply","support","sales","info","feedback","noreply",\
"docs.google.com", "craigslist.org"]

AWS_KEY = "AKIAIKCNCKG6RXJHWNFA"
AWS_SECRET = "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"
AWS_BUCKET = "aconn"

SCRAPING_API_KEY = "0ca62d4f6c0345ef80af1c4a9868da0f"

user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
GLOBAL_HEADERS ={'User-Agent':user_agent, 'Accept-Language': 'en-US,en;q=0.8', "Content-Language":"en"}

new_redis_host='129.41.154.147'
new_redis_dbname=0
new_redis_port=6379
new_redis_password='d78bde1a8e50bd337323fdfcda13dcbd'

bing_api_keys = ["xmiHcP6HHtkUtpRk/c6o9XCtuVvbQP3vi4WSKK1pKGg","VnjbIn8siy+aS9U2hjEmBgBGyhmiShWaTBARvh8lR1s","ETjsWwqMuHtuwV0366GtgJEt57BkFPbhnV4oT8lcfgU","CAkR9NrxB+9brLGVtRotua6LzxC/nZKqKuclWf9GjKU","hysOYscBLj0xtRDUst5wJLj2vWLyiueCDof6wGYD5Ls","FWyMRXjzB9NT1GXTFGxIdS0JdG3UsGHS9okxGx7mKZ0","U7ObwzZDTxyaTPbqwDkhPJ2wy+XfgMuVJ7k2BR/8HcE","VzTO15crpGKTYwkA8qqRThohTliVQTznqphD+WA5eVA"]
pub_profile_re = '^https*?://(www.)*linkedin.com/pub(?!/dir/)(/.*)+'
in_profile_re = '^https*?://(www.)*linkedin.com/in/.*'
profile_re = '(' + pub_profile_re + ')|(' + in_profile_re +')'
bloomberg_company_re = '^http://www.bloomberg.com/research/stocks/private/snapshot.asp\?privcapid=[0-9]+'
plus_company_re = '^https://plus.google.com/[0-9a-zA-Z]+/about'
school_re = '^https://www.linkedin.com/edu/*'
company_re = '^https://www.linkedin.com/company/*'

SOCIAL_DOMAINS = ["twitter","soundcloud","slideshare","plus","pinterest","facebook","linkedin","amazon","angel","foursquare","github","flickr"]
