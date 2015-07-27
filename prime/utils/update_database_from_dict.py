
from prime.prospects import models
from sqlalchemy.orm import joinedload
from consume.consumer import update_prospect_from_info, create_prospect_from_info

def insert_linkedin_profile(info, session):
	linkedin_id = info.get("linkedin_id")
	prospect = session.query(models.Prospect).filter_by(linkedin_id=linkedin_id).options(joinedload(models.Prospect.schools).joinedload(models.Education.school), joinedload(models.Prospect.jobs).joinedload(models.Job.company)).first()
	if prospect: 
		new_prospect = update_prospect_from_info(info, prospect, session=session)
	else:
		new_prospect = create_prospect_from_info(info, info.get("source_url"), session=session)
	if session.query(models.ProspectUrl).get(info.get("source_url")) is None:
		session.add(models.ProspectUrl(url=info.get("source_url"), linkedin_id=linkedin_id))
	session.commit()
	return new_prospect