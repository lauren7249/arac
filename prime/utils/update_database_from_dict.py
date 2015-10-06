
from prime.prospects.models import LinkedinSchool, LinkedinCompany, Prospect, Education, ProspectUrl, Job
from sqlalchemy.orm import joinedload
from consume.consumer import update_prospect_from_info, create_prospect_from_info

def insert_linkedin_profile(info, session):
	educations = info.get("schools")
	for education in educations:
		if education.get("college_id") and session.query(LinkedinSchool).get(education.get("college_id")) is None:
			session.add(LinkedinSchool(id=education.get("college_id"), name=education.get("college"), image_url=education.get("college_image_url")))	
	jobs = info.get("experiences")
	for job in jobs:
		if job.get("company_id") and session.query(LinkedinCompany).get(job.get("company_id")) is None:
			session.add(LinkedinCompany(id=job.get("company_id"), name=job.get("company"), image_url=job.get("company_image_url")))				
	linkedin_id = info.get("linkedin_id")
	prospect = session.query(Prospect).filter_by(linkedin_id=linkedin_id).options(joinedload(Prospect.schools).joinedload(Education.school), joinedload(Prospect.jobs).joinedload(Job.company)).first()
	if prospect: 
		new_prospect = update_prospect_from_info(info, prospect, session=session)
	else:
		new_prospect = create_prospect_from_info(info, info.get("source_url"), session=session)
	if session.query(ProspectUrl).get(info.get("source_url")) is None:
		session.add(ProspectUrl(url=info.get("source_url"), linkedin_id=linkedin_id))
	session.commit()
	return new_prospect

def insert_linkedin_company(info, session):
	record = session.query(LinkedinCompany).get(info.get("id")) 
	if not record:
		record = LinkedinCompany(id=info.get("id"))
	for key, value in info.iteritems():
	    setattr(record, key, value)
	session.add(record)
	if info.get("source_url") and session.query(LinkedinCompanyUrl).get(info.get("source_url")) is None:
		session.add(LinkedinCompanyUrl(url=info.get("source_url"), company_id=info.get("id")))
	session.commit()
	return record