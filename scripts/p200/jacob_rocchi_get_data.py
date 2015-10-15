from consume.facebook_friend import *
from consume.linkedin_friend import *
from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
from prime.utils.bing import *
from prime.utils import *

#get clients linkedin profile
client_linkedin_id = '67910358'
fbscraper = FacebookFriend()
liscraper = LinkedinFriend()

#figure out the linkedin connections and get their public links
client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json
linkedin_friends = liscraper.get_second_degree_connections(client_linkedin_id)
client_json["first_degree_linkedin_ids"] = linkedin_friends
client_linkedin_contact.json = client_json
session.add(client_linkedin_contact)
session.commit()

#scrape links
for linkedin_id in linkedin_friends:
	if from_linkedin_id(linkedin_id): 
		continue
	url = liscraper.get_public_link(linkedin_id)
	if url: r.sadd("urls",url)

client_facebook_id = 'jake.rocchi'

#get facebook friends
client_facebook_contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + client_facebook_id, scroll_to_bottom=True)
client_facebook_profile = client_facebook_contact.get_profile_info
client_engagers = client_facebook_contact.get_recent_engagers
client_engagers = fbscraper.get_likers(client_facebook_contact)
facebook_friends = fbscraper.scrape_profile_friends(client_facebook_contact)

#scrape facebook pages of friends
for username in facebook_friends:
	fbscraper.get_facebook_contact("https://www.facebook.com/" + username)