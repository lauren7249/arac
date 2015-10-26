from prime.prospects.models import *
from prime.utils.networks import clean_profile, get_mailto, get_salary_percentile
from consume.api_consumer import get_specific_url, get_pipl_images
from consume.get_gender import get_firstname, get_gender

class LeadProfile(db.Model):
    __tablename__ = "lead_profiles"
    id = db.Column(CIText(), primary_key=True)
    agent_id = db.Column(CIText(), ForeignKey("agent.email"), primary_key=True)
    agent = relationship('Agent', foreign_keys='LeadProfile.agent_id')    
    facebook_id = db.Column(CIText(), ForeignKey("facebook_contacts.facebook_id"), index=True)
    contact = relationship('FacebookContact', foreign_keys='LeadProfile.facebook_id')
    prospect_id = db.Column(Integer, ForeignKey("prospect.id"), index=True)
    prospect = relationship('Prospect', foreign_keys='LeadProfile.prospect_id')
    salary = db.Column(Integer)
    age = db.Column(Float)
    wealthscore = db.Column(Integer)
    leadscore = db.Column(Integer)
    mailto = db.Column(CIText())
    friend_prospect_ids = db.Column(JSON)
    people_links = db.Column(JSON)
    name = db.Column(String(200))
    twitter = db.Column(CIText())
    soundcloud = db.Column(CIText())
    slideshare = db.Column(CIText())
    plus = db.Column(CIText())
    pinterest = db.Column(CIText())
    facebook = db.Column(CIText())
    linkedin = db.Column(CIText())
    amazon= db.Column(CIText())
    angel= db.Column(CIText())
    foursquare= db.Column(CIText())
    github= db.Column(CIText())
    url = db.Column(CIText())
    location = db.Column(String(200))
    industry = db.Column(String(200))
    industry_category = db.Column(String(100))
    industry_icon = db.Column(String(40))
    job_title = db.Column(String(200))
    job_location = db.Column(String(200))
    company_name = db.Column(String(200))
    company_url = db.Column(CIText())
    company_website = db.Column(CIText())
    company_headquarters = db.Column(String(500))
    phone = db.Column(CIText())
    image_url = db.Column(CIText())
    gender = db.Column(String(15))
    college_grad = db.Column(Boolean)
    common_school = db.Column(String(200))
    extended = db.Column(Boolean)
    referrer_url =db.Column(CIText())
    referrer_name =db.Column(String(200))
    referrer_id = db.Column(CIText())
    referrer_connection =db.Column(String(600))
    json = db.Column(JSON)

    @staticmethod
    def validate_lead(prospect, exclude=[], schools=[], locations=[], associated_emails_dict={}, titles=[]):
		location = prospect.get_location
		if not location: 
			print "no location"
			return False				
		if locations and location not in locations:
			print location.encode('utf-8') + " not local" 
			return False
		# print prospect.id
		# import pdb
		# pdb.set_trace()
		job = prospect.get_job	
		if not job: 
			print "no job " + prospect.url.encode('utf-8')
			return False
		if job.get("company") in exclude: 
			print job.get("company").encode('utf-8') + " at the same company " 
			return False
		if titles and job.get("title") and job.get("title") not in titles:
			print job.get("title").encode('utf-8') + " not a qualified title"
			return False
		profile = clean_profile(prospect.build_profile)	
		if not profile.get("url"): 
			print "url is broken for " + str(profile["id"])
			return False 	
		profile["prospect_id"] = profile.get("id")	
		prospect_schools = [school.name for school in prospect.schools]
		profile["industry"] = prospect.industry_raw
		profile["age"] = prospect.age
		profile["people_links"] = prospect.json.get("people",[]) if prospect.json else []
		profile["college_grad"] = prospect.has_college_degree
		if job.get("company_url"):
			profile["company_url"] = job.get("company_url")
		if job.get("location"):
			profile["job_location"] = job.get("location")

		firstname = get_firstname(profile["name"])
		is_male = get_gender(firstname)
		if is_male is None: 
			profile["gender"] = "Unknown"
		elif is_male: 
			profile["gender"] = "Male"
		else: 
			profile["gender"] = "Female"

		jobtitle = session.query(JobTitle).get(job.get("title"))
		salary = max(jobtitle.glassdoor_salary,jobtitle.indeed_salary)

		profile["location"] = location
		profile["salary"] = salary
		associated_emails = associated_emails_dict.get(str(prospect.id),[])
		emails = [x for x in associated_emails if not x.endswith("@facebook.com") and x !='linkedin']
		profile["emails"] = emails
		profile["mailto"] = 'mailto:' + ",".join(emails)	

		social_accounts = prospect.social_accounts
		if salary:
			wealth_percentile = get_salary_percentile(salary)
			if wealth_percentile: 
				profile["wealthscore"] = wealth_percentile
		else:
			salary = 0
		n_social_accounts = len(social_accounts)
		score = n_social_accounts + salary/30000 
		amazon = get_specific_url(social_accounts, type="amazon.com")
		if amazon: score += 2	
		if profile.get("school") not in schools: profile.pop("school", None)
		if not profile.get("school") and prospect_schools: 
			common_schools = set(prospect_schools) & set(schools)
			if common_schools:
				profile["common_school"] = common_schools.pop()
				score+=1
		if profile.get("job_title") and profile.get("job_title").find("Financial") > -1: score-=4
		if associated_emails_dict:
			score+=(len(associated_emails)*2)
			if 'linkedin' in associated_emails: score+=6
		profile.update({"leadscore":score})		
		return profile

    @property 
    def categorize_industry(self):
        if not self.industry_category and industry_category.get(self.industry):
            self.industry_category = industry_category.get(self.industry)
            if not self.industry_icon and category_icon.get(self.industry_category):
                self.industry_icon = category_icon.get(self.industry_category)
            session.add(self)
            session.commit()

    @property 
    def get_images(self):
        images = []
        images = images+ get_pipl_images(self.prospect.get_pipl_response)
        if not self.mailto:
            return images
        email_accounts = self.mailto.split(":")[1].split(",")
        for email in email_accounts:
            email_contact = get_or_create(session,EmailContact, email=email)
            images = images + email_contact.get_images
        return images

    @property 
    def to_json(self):
        keep_vars = ["company_name", "job_title","name","leadscore","id","image_url","url","industry_category","mailto","phone","referrer_url","referrer_name","referrer_connection"]
        if self.json:
            return self.json
        keep_vars = keep_vars + social_domains      
        d = {}
        for column in self.__table__.columns:
            attr = getattr(self, column.name) 
            if column.name in keep_vars and attr is not None: 
                if isinstance(attr, basestring) and attr.find("http") == 0:
                    if not link_exists(attr): 
                        setattr(self, column.name, None)
                        continue        
                d[column.name] = attr
        if not self.image_url:
            for image in self.get_images:
                if link_exists(image):
                    self.image_url = image
                    d["image_url"] = self.image_url
                    break
        if not self.image_url:
            self.leadscore-=5
            self.image_url = "https://myspace.com/common/images/user.png"
            d["image_url"] = self.image_url
        self.json = d
        session.add(self)
        session.commit()    
        if d.get("leadscore") is None:
            print self.id        
        return d     

class CloudspongeRecord(db.Model):
    __tablename__ = "cloudsponge_raw"
    id = db.Column(Integer, primary_key=True)
    user_email = db.Column(CIText(), ForeignKey("agent.email"), index=True)
    agent = relationship('Agent', foreign_keys='CloudspongeRecord.user_email')
    contacts_owner = db.Column(JSON)
    contact = db.Column(JSON)
    service = db.Column(CIText())

    @property
    def get_job_title(self):
        return self.contact.get("job_title")

    @property
    def get_company(self):
        if self.contact.get("companies"):
            return self.contact.get("companies")[0]
        return None

    @property
    def get_emails(self):
        all_emails = []
        info = self.contact 
        emails = info.get("email",[{}])
        for email in emails:
            address = email.get("address").lower()
            if address: all_emails.append(address)
        return all_emails        