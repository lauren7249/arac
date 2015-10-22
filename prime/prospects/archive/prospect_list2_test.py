from prime.prospects.models import db, Prospect
from prime.prospects.prospect_list2 import ProspectList

session = db.session
url = "http://www.linkedin.com/pub/jimmy-lyons/41/7b9/968"
prospect = session.query(Prospect).filter_by(s3_key=url.replace("/", "")).first()
plist = ProspectList(prospect)
plist.get_results()