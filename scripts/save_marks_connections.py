linkedin_id='147893054'
from consume.linkedin_friend import *
from prime.prospects.get_prospect import *
from prime.prospects.models import *
from prime.utils import r
ig = LinkedinFriend(username="jeff@advisorconnect.co", password="1250downllc")
ig.login()
friends = set(ig.get_second_degree_connections(linkedin_id))
friend_urls = []
for friend in friends:
	url = ig.get_public_link(friend)
	if url and len(url): friend_urls.append(url)
prospect = from_linkedin_id(linkedin_id)
prospect_json = prospect.json
prospect_json["first_degree_linkedin_ids"] = list(friends)
prospect_json["first_degree_urls"] = friend_urls
session.query(Prospect).filter_by(id=prospect.id).update({"json":prospect_json})
session.commit()
for url in urls:
	r.lpush("urls",url)
