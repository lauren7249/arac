from consume.facebook_friend import *
from prime.prospects.models import *

fbscraper = FacebookFriend()
chris = session.query(FacebookContact).get("chris.biren")

for username in chris.get_friends():
	username = fbscraper.scrape_profile("https://www.facebook.com/" + username)
	#fbscraper.scrape_profile_friends(username)

