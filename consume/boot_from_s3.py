from prime.prospects.get_prospect import *
from prime.prospects.prospect_list2 import *
from boto.s3.key import Key
from prime.prospects.models import *

def boost(linkedin_id):
	setup()
	session = get_session()
	k = Key(bucket)
	k.key = "entities/prospects/linkedin_id/" +  str(linkedin_id) + "/linkedin_ids.csv"
	contents = k.get_contents_as_string()
	friend_set = set(contents.split("\n"))
	friend_set.remove('')
	friend_list = list(friend_set)
	prospect = from_linkedin_id(linkedin_id)
	user_json = prospect.json if prospect.json else {}
	user_json['boosted_ids'] = friend_list
	session.query(Prospect).filter(Prospect.id == prospect.id).update({
	    "json":user_json
	    })
	session.commit()