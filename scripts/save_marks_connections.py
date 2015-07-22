linkedin_id='301173'
from consume.linkedin_friend import *
from prime.prospects.get_prospect import *
from prime.prospects.models import *
ig = LinkedinFriend(username="jeff@advisorconnect.co", password="1250downllc")
friends = set(ig.get_second_degree_connections(linkedin_id))
prospect = from_linkedin_id(linkedin_id)
prospect_json = prospect.json
prospect_json["first_degree_linkedin_ids"] = list(friends)
session.query(Prospect).filter_by(id=prospect.id).update({"json":prospect_json})
session.commit()