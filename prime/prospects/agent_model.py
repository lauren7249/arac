from prime.prospects.models import *
from prime.prospects.lead_model import *
from sqlalchemy import or_, and_
from prime.utils import bing
from prime.prospects.get_prospect import connected
from prime.utils.geocode import GeoPoint

class Agent(db.Model):
    __tablename__ = "agent"
    email = db.Column(CIText(), primary_key=True)
    geolocation = db.Column(CIText())
    public_url = db.Column(CIText())
    first_name = db.Column(CIText())
    unique_emails = db.Column(JSON)
    linkedin_urls = db.Column(JSON)
    extended_urls = db.Column(JSON)
    prospect_ids = db.Column(JSON)
    company_exclusions = db.Column(JSON)
    #only local to the agent
    first_degree_locations = db.Column(JSON)
    extended_locations = db.Column(JSON)
    #only within the income threshold
    first_degree_titles = db.Column(JSON)
    extended_titles = db.Column(JSON)   

    extended_prospect_ids = db.Column(JSON)

    qualified_leads_determined = db.Column(Boolean)
    extended_leads_determined = db.Column(Boolean)

    average_age = db.Column(Float) 
    average_wealth_score = db.Column(Float) 
    pct_college = db.Column(Float) 
    pct_male = db.Column(Float) 
    pct_female = db.Column(Float) 
    industries = db.Column(JSON) 
    schools = db.Column(JSON) 
    n_qualified_leads= db.Column(Integer) 
    n_extended_leads  =db.Column(Integer) 
    leads_json  =db.Column(JSON) 
    extended_leads_json  =db.Column(JSON) 

    @property 
    def get_extended_prospects(self):
        prospect_ids=[int(x) for x in self.get_extended_prospect_ids.keys()]
        prospect_ids.sort()
        prospects =  session.query(Prospect).filter(Prospect.id.in_(prospect_ids)).all()
        return prospects

    @property 
    def get_prospects(self):
        prospect_ids=[int(x) for x in self.get_prospect_ids.keys()]
        prospect_ids.sort()
        prospects =  session.query(Prospect).filter(Prospect.id.in_(prospect_ids)).all()
        return prospects

    @property 
    def get_extended_leads(self):
        if self.extended_leads_determined:
            return session.query(LeadProfile).filter(and_(LeadProfile.agent_id==self.email,LeadProfile.extended.is_(True))).all() 
        prospect_ids = self.get_prospect_ids.keys()
        locations = self.get_extended_locations
        titles = self.get_extended_titles
        exclusions = self.company_exclusions
        contact_profiles = self.get_qualified_leads
        self.get_extended_prospect_ids
        me = from_url(self.public_url)
        extended_profiles = []
        for profile in contact_profiles:
            if not profile.friend_prospect_ids: continue
            for prospect_id in profile.friend_prospect_ids:
                if prospect_id in prospect_ids: continue
                if prospect_id==me.id: continue
                li = from_prospect_id(prospect_id)
                commonality = profile.friend_prospect_ids.get(prospect_id)
                valid_profile = LeadProfile.validate_lead(li, exclude=exclusions, locations=locations, titles=titles)
                if not valid_profile: 
                    continue
                valid_profile["referrer_id"] = profile.id
                valid_profile["referrer_url"] = profile.url
                valid_profile["referrer_name"] = profile.name
                valid_profile["referrer_connection"] = commonality 
                valid_profile["extended"] = True       
                extended_profiles.append(valid_profile)   
        session.commit()
        cp = []
        for valid_profile in extended_profiles:
            lead = get_or_create(session,LeadProfile,agent_id=self.email, id=str(valid_profile.get("id")))
            for key, value in valid_profile.iteritems():
                setattr(lead, key, value)       
            session.add(lead)   
            cp.append(lead)
        self.extended_leads_determined = True
        session.add(self)
        session.commit()                              
        return cp

    @property 
    def get_extended_prospect_ids(self):
        if self.extended_prospect_ids:
            return self.extended_prospect_ids
        contact_profiles = self.get_qualified_leads
        linkedin_urls = self.get_linkedin_urls.keys()
        pairs = []
        session.commit()
        for profile in contact_profiles:        
            if not profile.prospect:
                continue
            profile.friend_prospect_ids = {}
            print profile.id
            if profile.headline:
                urls = set(bing.search_extended_network(profile.name, school=profile.headline) + profile.people_links)
            elif profile.company_name:
                urls = set(bing.search_extended_network(profile.name, school=profile.company_name) + profile.people_links)
            else:
                urls = set(bing.search_extended_network(profile.name, school=profile.job_title) + profile.people_links)   
            for url in urls:
                if url in linkedin_urls: 
                    continue           
                extended_prospect = from_url(url)
                if not extended_prospect or str(extended_prospect.id) in self.get_prospect_ids.keys():
                    continue
                pairs.append((profile.prospect,extended_prospect))
        # pool = multiprocessing.Pool(15)
        # results = pool.map(has_common_inst, pairs)
        # pool.close()
        extended_prospect_ids = {}
        for i in xrange(0, len(pairs)):
            #commonality = results[i]
            pair = pairs[i] 
            commonality = connected(pair)
            if not commonality: 
                continue  
            prospect = pair[0]
            extended_prospect = pair[1]
            #really just a get
            profile = get_or_create(session, LeadProfile,agent_id=self.email, id=str(prospect.id))
            friend_prospect_ids = profile.friend_prospect_ids if profile.friend_prospect_ids else {}
            friend_prospect_ids.update({extended_prospect.id: commonality})
            profile.friend_prospect_ids = friend_prospect_ids
            session.add(profile)
            referrers = extended_prospect_ids.get(extended_prospect.id, [])
            referrers.append((prospect.id,commonality))
            extended_prospect_ids.update({extended_prospect.id: referrers})
        self.extended_prospect_ids = extended_prospect_ids
        session.add(self)
        session.commit()
        return extended_prospect_ids

    @property 
    def get_extended_urls(self):
        if self.extended_urls:
            return self.extended_urls
        contact_profiles = self.get_qualified_leads
        linkedin_urls = self.get_linkedin_urls.keys()
        extended_urls = set()
        for profile in contact_profiles:
            #print profile.id
            if profile.headline:
                urls = set(bing.search_extended_network(profile.name, school=profile.headline) + profile.people_links)
            elif profile.company_name:
                urls = set(bing.search_extended_network(profile.name, school=profile.company_name) + profile.people_links)
            else:
                urls = set(bing.search_extended_network(profile.name, school=profile.job_title) + profile.people_links)
            for url in urls:
                if url not in linkedin_urls: extended_urls.add(url)
            #print str(len(extended_urls)) + " extended urls"
        extended_urls = list(extended_urls)
        self.extended_urls = extended_urls
        session.add(self)
        session.commit()
        return extended_urls

    @property 
    def get_qualified_leads(self):
        prospect_ids = self.get_prospect_ids
        if self.qualified_leads_determined:
            return session.query(LeadProfile).filter(and_(LeadProfile.agent_id==self.email,not_(LeadProfile.extended.is_(True)))).all() 
        exclusions = self.company_exclusions
        p = from_url(self.public_url)
        prospects = self.get_prospects
        prospect_ids = self.get_prospect_ids
        client_schools = [school.name for school in p.schools]
        locations = self.get_first_degree_locations
        titles = self.get_first_degree_titles
        contact_profiles = []
        for prospect_id in prospect_ids:
            prospect = from_prospect_id(int(prospect_id))
            valid_profile = LeadProfile.validate_lead(prospect, exclude=exclusions, schools=client_schools, locations=locations, associated_emails_dict=prospect_ids, titles=titles)
            if valid_profile:
                contact_profiles.append(valid_profile)
        session.commit()
        cp = []
        for valid_profile in contact_profiles:
            lead = get_or_create(session,LeadProfile,agent_id=self.email, id=str(valid_profile.get("id")))
            for key, value in valid_profile.iteritems():
                setattr(lead, key, value)       
            session.add(lead)   
            cp.append(lead)
        self.qualified_leads_determined = True
        session.add(self)
        session.commit()
        return cp

    @staticmethod
    def compute_stars(contact_profiles):
        all_scores = [profile.get("leadscore") for profile in contact_profiles]
        for i in range(len(contact_profiles)):
            profile = contact_profiles[i]
            percentile = stats.percentileofscore(all_scores, profile["leadscore"])
            if percentile > 66: score = 3
            elif percentile > 33: score = 2
            else: score = 1
            profile["score"] = score
            contact_profiles[i] = profile
        contact_profiles = sorted(contact_profiles, key=lambda k: k['leadscore'], reverse=True) 
        return contact_profiles

    @staticmethod
    def only_real_jobs(qualified_titles):
        qualified_titles = set(qualified_titles)
        #TODO: use natural language processing
        not_real_job_words = ["intern","candidate","student","summer","part-time"]
        for title in qualified_titles.copy():
            for word in not_real_job_words:
                regex = "(\s|^)" + word + "(,|\s|$)"
                if re.search(regex, title.lower()):
                    print uu(title + " not a real job")
                    qualified_titles.remove(title)
                    break
        return list(qualified_titles)

    @property 
    def get_extended_titles(self):
        if self.extended_titles:
            return Agent.only_real_jobs(self.extended_titles)
        prospects = self.get_extended_prospects
        qualified_job_titles = Agent.get_qualified_job_titles(prospects)
        self.extended_titles = qualified_job_titles
        session.add(self)
        session.commit()
        return Agent.only_real_jobs(qualified_job_titles)

    @property 
    def get_first_degree_titles(self):
        if self.first_degree_titles:
            return Agent.only_real_jobs(self.first_degree_titles)
        prospects = self.get_prospects
        qualified_job_titles = Agent.get_qualified_job_titles(prospects)
        self.first_degree_titles = qualified_job_titles
        session.add(self)
        session.commit()
        return Agent.only_real_jobs(qualified_job_titles)

    @staticmethod
    def get_qualified_job_titles(prospects, threshold_salary=36000):
        qualified_titles = set()
        titles = set()
        for prospect in prospects:
            title = prospect.get_job.get("title")           
            if title:
                titles.add(title)
        salaried = session.query(JobTitle).filter(and_(JobTitle.title.in_(list(titles)), or_(JobTitle.glassdoor_salary !=None, JobTitle.indeed_salary !=None))).all()
        for current_job in salaried:
            if current_job.glassdoor_salary and current_job.glassdoor_salary>=threshold_salary:
                qualified_titles.add(current_job.title)
                continue
            if current_job.indeed_salary and current_job.indeed_salary>=threshold_salary:
                qualified_titles.add(current_job.title)
                continue   
        for_indeed = list(titles - qualified_titles)
        print str(len(for_indeed)) + " for_indeed"
        if len(for_indeed):
            pool = multiprocessing.Pool(15)    
            indeed_salaries = pool.map(get_indeed_salary, for_indeed)
            print "done getting indeed"
            pool.close()
        for i in xrange(0, len(for_indeed)):
            title = for_indeed[i]
            salary = indeed_salaries[i]
            record = get_or_create(session,JobTitle,title=title)
            record.indeed_salary = salary
            session.add(record)     
            if salary>=threshold_salary:
                qualified_titles.add(title)
        session.commit()                
        for_glassdoor = list(titles - qualified_titles)
        print str(len(for_glassdoor)) + " for_glassdoor"
        if len(for_glassdoor):
            pool = multiprocessing.Pool(15)    
            glassdoor_salaries = pool.map(get_glassdoor_salary, for_glassdoor)
            print "done getting glassdoor"
            pool.close()
        for i in xrange(0, len(for_glassdoor)):
            title = for_glassdoor[i]
            salary = glassdoor_salaries[i]
            record = get_or_create(session,JobTitle,title=title)
            record.glassdoor_salary = salary
            session.add(record)     
            if salary>=threshold_salary:
                qualified_titles.add(title)
            #neither search engine found the title. must be pretty specialized. we will assume it qualifies.
            elif record.glassdoor_salary==-1 and record.indeed_salary==-1:
                qualified_titles.add(title)
            else:
                print uu(title + " not high enough salary")
        session.commit()
        return list(qualified_titles)

    @staticmethod
    def get_local_locations(propsect_ids_json, client_geopoint, threshold_miles=50):
        from prime.utils.geocode import search_mapquest_coordinates
        prospect_ids = []
        for prospect_id in propsect_ids_json.keys():
            prospect_ids.append(int(prospect_id))
        prospect_ids.sort()
        prospect_locations =  session.query(Prospect.location_raw).filter(Prospect.id.in_(prospect_ids)).distinct().all()
        unique_locations = set()
        for rec in prospect_locations:
            location = rec.location_raw
            if location:
                unique_locations.add(location)         
        geocoded = session.query(MapquestGeocodes).filter(and_(MapquestGeocodes.name.in_(list(unique_locations)), MapquestGeocodes.geocode !=None)).all()
        local_locations = []      
        geocoded_names = set()    
        for record in geocoded:
            mapquest_info = record.geocode
            name = record.name
            geocoded_names.add(name)
            if not mapquest_info:
                continue
            latlng = mapquest_info.get("latlng")
            if not latlng:
                continue
            geopoint = GeoPoint(latlng[0],latlng[1])    
            miles_apart = geopoint.distance_to(client_geopoint)    
            if miles_apart<=threshold_miles:
                local_locations.append(name)
        print str(len(unique_locations)) + " unique_locations"
        new_locations = list(unique_locations - geocoded_names)
        print str(len(new_locations)) + " new_locations"
        pool = multiprocessing.Pool(15)    
        mapquest_coords = pool.map(search_mapquest_coordinates, new_locations)
        print "done getting coordinates"
        pool.close()
        for i in xrange(0, len(new_locations)):
            location = new_locations[i]
            mapquest_info = mapquest_coords[i]
            record = get_or_create(session,MapquestGeocodes,name=location)
            record.geocode = mapquest_info
            session.add(record)
            latlng = mapquest_info.get("latlng")
            if not latlng:
                continue
            geopoint = GeoPoint(latlng[0],latlng[1])    
            miles_apart = geopoint.distance_to(client_geopoint)    
            if miles_apart<threshold_miles:
                local_locations.append(location)    
        session.commit()
        return local_locations

    @property 
    def get_first_degree_locations(self):
        if self.first_degree_locations:
            return self.first_degree_locations
        client_geopoint = self.get_geopoint
        local_locations = Agent.get_local_locations(self.get_prospect_ids, client_geopoint)
        if local_locations:
            self.first_degree_locations = local_locations
            session.add(self)
            session.commit()    
        return local_locations

    @property 
    def get_extended_locations(self):
        if self.extended_locations:
            return self.extended_locations
        client_geopoint = self.get_geopoint
        local_locations = Agent.get_local_locations(self.get_extended_prospect_ids, client_geopoint)
        if local_locations:
            self.extended_locations = local_locations
            session.add(self)
            session.commit()    
        return local_locations

    @property 
    def get_geopoint(self):
        client_coords = MapquestGeocodes.get_coordinates(self.geolocation, use_db=True).get("latlng")
        client_geopoint = GeoPoint(client_coords[0],client_coords[1])     
        return client_geopoint

    @property 
    def get_prospect_ids(self):
        if self.prospect_ids:
            return self.prospect_ids
        prospect_ids = {}
        linkedin_urls = self.get_linkedin_urls
        for url in linkedin_urls.keys():
            contact = from_url(url)
            if not contact: 
                continue
            urls_associated_emails = linkedin_urls.get(url,[])
            prospects_associated_emails = prospect_ids.get(contact.id,[])
            associated_emails = list(set(urls_associated_emails+prospects_associated_emails))
            prospect_ids[contact.id] = associated_emails
            contact_email_addresses = contact.all_email_addresses
            if 'linkedin' in associated_emails:
                associated_emails.remove('linkedin')
            contact.all_email_addresses = list(set(associated_emails + contact_email_addresses)) if contact_email_addresses else associated_emails
            session.add(contact)
        self.prospect_ids = prospect_ids
        session.add(self)
        session.commit()    
        return prospect_ids

    @property 
    def get_linkedin_urls(self):
        if self.linkedin_urls:
            return self.linkedin_urls
        unique_emails = self.get_email_contacts
        linkedin_urls = {}
        for_pipl = []
        for email in unique_emails.keys():
            info = unique_emails.get(email,{})
            sources = info.get("sources",set()) 
            url = info.get("linkedin")
            ec = get_or_create(session,EmailContact,email=email)    
            if not url and ec.linkedin_url:
                url = ec.linkedin_url
            elif ec.pipl_response and ec.pipl_response.get("@http_status_code")!=403:
                url = ec.get_linkedin_url
            if url:
                if not ec.linkedin_url:
                    ec.linkedin_url = url
                    session.add(ec)
                    session.commit()
                associated_emails = linkedin_urls.get(url,[])
                if email not in associated_emails: 
                    associated_emails.append(email)
                if 'linkedin' in sources and 'linkedin' not in associated_emails: 
                    associated_emails.append('linkedin')
                linkedin_urls[url] = associated_emails          
                info["linkedin"] = ec.linkedin_url
                unique_emails[email] = info 
                continue
            else:
                for_pipl.append(email)
        print str(len(linkedin_urls)) + " linkedin urls already known"
        print str(len(for_pipl)) + " for pipl to check"
        #pipl limits you to 20 hits/second. if you go above a pool size of 5, this could be an issue.
        pool = multiprocessing.Pool(5)
        pipl_responses = pool.map(query_pipl, for_pipl)
        for_clearbit = []
        for i in xrange(0, len(for_pipl)):
            email = for_pipl[i]
            info = unique_emails.get(email,{})
            sources = info.get("sources",set()) 
            ec = session.query(EmailContact).get(email)
            pipl_response = pipl_responses[i] if pipl_responses[i].get("@http_status_code")!=403 else ec.get_pipl_response
            ec.pipl_response = pipl_response
            pipl_social_accounts = get_pipl_social_accounts(pipl_response)
            url = get_specific_url(pipl_social_accounts, type="linkedin.com")
            if url:
                ec.linkedin_url = url
                associated_emails = linkedin_urls.get(url,[])
                if email not in associated_emails: 
                    associated_emails.append(email)
                if 'linkedin' in sources and 'linkedin' not in associated_emails: 
                    associated_emails.append('linkedin')
                linkedin_urls[url] = associated_emails          
                info["linkedin"] = url
                unique_emails[email] = info             
                continue
            if not ec.clearbit_response:
                for_clearbit.append(email)
            session.add(ec)
        session.commit()
        print str(len(linkedin_urls))+  " linkedin urls found so far"
        print str(len(for_clearbit)) +" for clearbit to check"
        pool = multiprocessing.Pool(10)
        clearbit_responses = pool.map(query_clearbit, for_clearbit)
        pool.close()
        for i in xrange(0, len(for_clearbit)):
            email = for_clearbit[i]
            info = unique_emails.get(email,{})
            sources = info.get("sources",set()) 
            ec = session.query(EmailContact).get(email)
            clearbit_response = clearbit_responses[i]
            ec.clearbit_response = clearbit_response
            session.add(ec)
            clearbit_social_accounts = get_clearbit_social_accounts(clearbit_response)
            url = get_specific_url(clearbit_social_accounts, type="linkedin.com")
            if url:
                associated_emails = linkedin_urls.get(url,[])
                if email not in associated_emails: 
                    associated_emails.append(email)
                if 'linkedin' in sources and 'linkedin' not in associated_emails: 
                    associated_emails.append('linkedin')
                linkedin_urls[url] = associated_emails          
                info["linkedin"] = ec.linkedin_url
                unique_emails[email] = info             
                ec.linkedin_url = url
                session.add(ec)
        session.commit()
        self.unique_emails = unique_emails
        self.linkedin_urls = linkedin_urls
        session.add(self)
        session.commit()
        return linkedin_urls

    @property
    def get_email_contacts(self):
        unique_emails = {}       
        if self.unique_emails:
            return self.unique_emails
        contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email==self.email).all() 
        for contact in contacts:
            service = contact.service
            rec = contact.get_emails
            job_title = contact.get_job_title
            company = contact.get_company
            for email in rec:
                try:
                    domain = email.split("@")[-1].lower().strip()
                    if domain in ['docs.google.com'] or domain.find('craigslist.org')>-1:
                        print email + " not a person" 
                        continue            
                    not_a_person = False  
                    non_person_email_words = ["reply","support","sales","info","feedback","noreply"]        
                    for word in non_person_email_words:  
                        regex = '(\-|^|\.)' + word + '(\-|@|\.)'
                        if re.search(regex,email):
                            not_a_person = True
                            break
                    if not_a_person:
                        print email + " not a person" 
                        continue
                    info = unique_emails.get(email,{})
                    sources = info.get("sources",[])
                    if service.lower()=='linkedin':
                        if 'linkedin' not in sources: 
                            sources.append('linkedin')
                    elif contact.contacts_owner:
                        source = contact.contacts_owner.get("email",[{}])[0].get("address")
                        if source and source not in sources: 
                            sources.append(source)
                    info["sources"] = sources
                    if job_title: 
                        info["job_title"] = job_title
                    if company:
                        info["company"] = company
                    unique_emails[email] = info 
                except:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    exception_str = traceback.format_exception(*exc_info)                    
                    print email + " failed with error " + str(exception_str)
                    continue
        self.unique_emails = unique_emails
        session.add(self)
        session.commit()                  
        return unique_emails

    @property 
    def compute_stats(self):
        contact_profiles = session.query(LeadProfile).filter(LeadProfile.agent_id==self.email).all() 
        industries = {}
        schools = {}
        if len(contact_profiles) ==0 : return 
        n_degree = 0
        n_wealth = 0
        wealth_tot = 0
        n_age = 0
        age_tot = 0
        n_male = 0
        n_female = 0
        self.n_qualified_leads = 0
        self.n_extended_leads = 0
        for profile in contact_profiles:
            if profile.extended:
                self.n_extended_leads+=1
                continue
            self.n_qualified_leads+=1
            if profile.wealthscore: 
                n_wealth+=1
                wealth_tot+=profile.wealthscore 
            if profile.age:
                n_age+=1
                age_tot+=profile.age    
            if profile.college_grad:
                n_degree+=1
            if profile.gender:
                if profile.gender=='Male':
                    n_male+=1
                elif profile.gender=='Female':
                    n_female+=1
            if profile.common_school:
                count = schools.get(profile.common_school,0)
                schools[profile.common_school] = count+1   
            if profile.industry_category:
                count = industries.get(profile.industry_category,0)
                industries[profile.industry_category] = count+1                   
        self.average_age = float(age_tot)/float(n_age)
        self.average_wealth_score = float(wealth_tot)/float(n_wealth)
        self.pct_college = float(n_degree)/float(self.n_qualified_leads)
        self.pct_male = float(n_male)/float(n_male+n_female)
        self.pct_female = float(n_female)/float(n_male+n_female)
        self.industries = industries
        self.schools = schools
        session.add(self)
        session.commit()

    @property 
    def get_leads_json(self):
        if self.leads_json:
            return self.leads_json
        leads = []
        contact_profiles = session.query(LeadProfile).filter(and_(LeadProfile.agent_id==self.email, LeadProfile.extended.isnot(True))).all() 
        for profile in contact_profiles:
            profile.industry_category = None
            profile.industry_icon = None            
            profile.categorize_industry
            profile_json = profile.to_json
            if not profile_json.get("url"):
                continue               
            leads.append(profile_json)
            session.add(profile)
        self.leads_json = Agent.compute_stars(leads)
        session.add(self)
        session.commit()
        return leads

    @property 
    def get_extended_leads_json(self):
        if self.extended_leads_json:
            return self.extended_leads_json
        leads = []
        contact_profiles = session.query(LeadProfile).filter(and_(LeadProfile.agent_id==self.email, LeadProfile.extended.is_(True))).all() 
        for profile in contact_profiles:
            profile.industry_category = None
            profile.industry_icon = None            
            profile.categorize_industry
            profile_json = profile.to_json
            if not profile_json.get("url"):
                continue            
            leads.append(profile_json)
            session.add(profile)
        self.extended_leads_json = Agent.compute_stars(leads)
        session.add(self)
        session.commit()
        return leads

    @property 
    def top_industries(self):
        if not self.industries:
            return []
        return sorted(self.industries, key=self.industries.get, reverse=True)[:5]

    @property 
    def write_leads_js(self):
        base_dir = 'p200_templates/' + self.email
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)        
        js_dir = base_dir + "/js"
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
        leads_str = "connectionsJ = " + unicode(json.dumps(self.leads_json, ensure_ascii=False)) + "; "
        leads_file = open(js_dir + "/leads-ln.js", "w")
        leads_file.write(leads_str.encode('utf8', 'replace'))
        leads_file.close()
        leads_str = "connectionsJ = " + unicode(json.dumps(self.extended_leads_json, ensure_ascii=False)) + "; "
        leads_file = open(js_dir + "/leads-extended.js", "w")
        leads_file.write(leads_str.encode('utf8', 'replace'))
        leads_file.close()

    @property 
    def write_vars_js(self):
        base_dir = 'p200_templates/' + self.email
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)        
        js_dir = base_dir + "/js"
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
        vars_str = 'var colors = ["#8dd8f7", "#5bbdea", "#01a1dd", "#0079c2"]; function randColor(colors) {return colors[Math.floor(Math.random() * colors.length)]}  '
        vars_str += 'industries = ' + json.dumps(self.industries_json) + ";  "
        vars_str += 'var schools = ' + json.dumps(self.schools_json) + ";  "
        vars_str += 'var stats = ' + json.dumps(self.stats_json) + ";  "
        vars_str += 'var n_extended = ' + str(self.n_extended_leads) + ";  "
        vars_str += 'var n_first_degree = ' + str(self.n_qualified_leads) + ";  "
        vars_str += 'var n_total = ' + str(self.n_qualified_leads + self.n_extended_leads) + ";  "
        vars_str += 'client_name = "' + self.first_name + '";  '
        vars_file = open(js_dir + "/vars.js", "w")
        vars_file.write(vars_str)
        vars_file.close()

    @property 
    def write_html_files(self):
        base_dir = 'p200_templates/' + self.email
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)        
        from_dir = 'p200_templates/common' 
        shutil.copyfile(from_dir + "/leads.html", base_dir + "/leads-ln.html")     
        shutil.copyfile(from_dir + "/leads.html", base_dir + "/leads-extended.html")     
        shutil.copyfile(from_dir + "/summary.html", base_dir + "/summary.html")     
        for category in self.top_industries:
            clean = re.sub("[^a-z]","", category.lower())  
            shutil.copyfile(from_dir + "/leads.html", base_dir + "/leads-" + clean + ".html")      

    @property 
    def create_visual(self):
        self.get_leads_json
        self.get_extended_leads_json           
        self.compute_stats   
        self.schools_json
        self.industries_json 
        self.write_html_files
        self.write_vars_js
        self.write_leads_js

    @property 
    def refresh_visual(self):
        self.leads_json = None
        self.extended_leads_json = None
        self.schools = None
        self.industries = None
        self.get_leads_json
        self.get_extended_leads_json 
        self.compute_stats        
        self.schools_json
        self.industries_json
        self.write_html_files
        self.write_vars_js
        self.write_leads_js

    @property 
    def stats_json(self):
        percent_male = "{0:.0f}%".format(self.pct_male*100)
        percent_female = "{0:.0f}%".format(self.pct_female*100)
        percent_degree = "{0:.0f}%".format(self.pct_college*100)
        average_age = int(self.average_age)
        average_wealth = str(int(self.average_wealth_score)) + "/100"
        stats = [{"name":"Male","value":percent_male},{"name":"Female","value":percent_female},{"name":"College Degree","value":percent_degree},{"name":"Average Income Score","value":average_wealth},{"name":"Average Age","value":average_age}]
        return stats

    @property 
    def schools_json(self):
        if not self.schools:
            return []
        school_info = []
        for school in self.schools:
            clean = re.sub("[^a-z]","", school.lower())
            count = self.schools[school]
            d = {'clean':clean,'label':school, 'value':count}
            school_info.append(d)
        return school_info

    @property 
    def industries_json(self):
        if not self.industries:
            return []
        top_industries = self.top_industries
        industry_info = []
        for category in top_industries:
            clean = re.sub("[^a-z]","", category.lower())
            count = self.industries[category]
            icon = category_icon[category]
            d = {'clean':clean,'label':category, 'value':count, 'icon':icon}
            industry_info.append(d)    
        return industry_info   