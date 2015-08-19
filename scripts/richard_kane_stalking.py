from prime.utils.googling import *
from prime.prospects.get_prospect import *
from prime.prospects.models import *
from consume.facebook_friend import *

fbscraper = FacebookFriend()

url = search_linkedin_profile("richard kane new york","richard kane", require_proxy=False)
client_linkedin_contact = from_url(url)
client_json = client_linkedin_contact.json

email_accounts = set()
social_accounts = set()
addresses = set()
zips = set()
images = set()

addresses.update(get_pipl_addresses(client_linkedin_contact.get_pipl_response))
zips.update(get_pipl_zips(client_linkedin_contact.get_pipl_response))
images.update(get_pipl_images(client_linkedin_contact.get_pipl_response))

for address in client_linkedin_contact.email_accounts:
	email_accounts.add(address)
	contact = session.query(EmailContact).get(address)
	if not contact: 
		contact = EmailContact(email=address)
	social_accounts.update(contact.social_accounts)
	addresses.update(get_pipl_addresses(contact.get_pipl_response))
	zips.update(get_pipl_zips(contact.get_pipl_response))
	images.update(get_pipl_images(contact.get_pipl_response))

facebook_url = get_specific_url(social_accounts, type='facebook')

client_facebook_contact = fbscraper.get_facebook_contact(facebook_url, scroll_to_bottom=True)
client_facebook_profile = client_facebook_contact.get_profile_info
images.add(client_facebook_profile.get("image_url"))
client_facebook_friends = fbscraper.scrape_profile_friends(client_facebook_contact)