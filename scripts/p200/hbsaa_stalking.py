from prime.utils.googling import *
from prime.prospects.get_prospect import *
from prime.prospects.models import *
from consume.facebook_friend import *
from consume.linkedin_friend import *
from __future__ import print_function
import os, re
import datetime
from prime.utils import *
from consume.angelist import *
from consume.convert import uu
from prime.utils.proxy_scraping import get_domain

fbscraper = FacebookFriend()
linkedinscraper = LinkedinFriend()

names = ["Richard Kane", "John Reese", "Douglas Libby","Bradley Schrader","Fu'ad Butt","Jim Sherman"]

for name in names:
	directory = "/Users/lauren/Documents/data/" + name

	if not os.path.exists(directory): os.makedirs(directory)
	filename = directory + "/" + name + ".txt" 
	if os.path.exists(filename): os.remove(filename)
	f = open(filename, 'ab')
	f.writelines(name)
	f.write("\n")

	url = search_linkedin_profile(name + " harvard",name, require_proxy=False)
	print(url)

	client_linkedin_contact = from_url(url)
	client_json = client_linkedin_contact.json

	print("\n\nLocation:\n\t" +client_linkedin_contact.location_raw, file=f)
	print("\n\nIndustry:\n\t"+ client_linkedin_contact.industry_raw, file=f)

	client_linkedin_id = str(client_linkedin_contact.linkedin_id)
	if client_linkedin_contact.connections == 500:
		count_client_linkedin_friends = linkedinscraper.count_second_degree_connections(client_linkedin_id)
		client_linkedin_contact.connections = count_client_linkedin_friends
		session.add(client_linkedin_contact)
		session.commit()

	print("\nLinkedin connections:\n\t"+ str(client_linkedin_contact.connections), file=f)	
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

	facebook_url = get_specific_url(social_accounts, type='facebook.com')

	if facebook_url:
		client_facebook_contact = fbscraper.get_facebook_contact(facebook_url, scroll_to_bottom=True)
		client_facebook_profile = client_facebook_contact.get_profile_info
		images.add(client_facebook_profile.get("image_url"))
		client_facebook_friends = fbscraper.scrape_profile_friends(client_facebook_contact)

		email_accounts.update(get_pipl_emails(client_facebook_contact.get_pipl_response))
		addresses.update(get_pipl_addresses(client_facebook_contact.get_pipl_response))
		zips.update(get_pipl_zips(client_facebook_contact.get_pipl_response))
		images.update(get_pipl_images(client_facebook_contact.get_pipl_response))
		social_accounts.update(get_pipl_social_accounts(client_facebook_contact.get_pipl_response))

		for address in get_pipl_emails(client_facebook_contact.get_pipl_response):
			contact = session.query(EmailContact).get(address)
			if not contact: 
				contact = EmailContact(email=address)
			social_accounts.update(contact.social_accounts)
			addresses.update(get_pipl_addresses(contact.get_pipl_response))
			zips.update(get_pipl_zips(contact.get_pipl_response))
			images.update(get_pipl_images(contact.get_pipl_response))

		if client_facebook_contact and client_facebook_contact.profile_info and client_facebook_contact.profile_info.get("friend_count"):
			print("\nFacebook friend count: " + str(client_facebook_contact.profile_info.get("friend_count")), file=f)

	if images:
		print("\nImages:", file=f)
		for image in images:
			if image: print("\t" + image, file=f)
	if email_accounts:
		print("\nEmail accounts:", file=f)
		for i in email_accounts:
			print("\t" + i, file=f)	
	if social_accounts:
		print("\nSocial accounts:", file=f)
		for i in social_accounts:
			print("\t" + i, file=f)	
	if addresses:
		print("\nAddresses:", file=f)
		for i in addresses:
			print("\t" + i, file=f)	
	if zips:
		print("\nZips:", file=f)
		for i in zips:
			print("\t" + i, file=f)	

	if client_json.get("groups"):
		print("\nGroups:", file=f)
		for i in client_json.get("groups"):
			print("\t" + uu(i.get("name")), file=f)	

	if client_json.get("skills"):
		print("\nSkills:", file=f)
		for i in client_json.get("skills"):
			print("\t" + uu(i), file=f)	

	first_year_experience = None
	if client_linkedin_contact.jobs:
		print("\nJobs:", file=f)
		for job in client_linkedin_contact.jobs:
			job_string = ""
			if job.company: job_string = job_string + job.company.name + ": " 
			if job.title: job_string = job_string + job.title + " " 
			if job.start_date: 
				if not first_year_experience or job.start_date.year<first_year_experience: first_year_experience = job.start_date.year
				job_string = job_string + "(" + str(job.start_date.year) + " - "
				if job.end_date: job_string = job_string + str(job.end_date.year) + ")"
				else: job_string = job_string + "?)"
			elif job.end_date: job_string = job_string + "(? - " + str(job.end_date.year) + ")"
			if job.location: job_string = job_string + ". " + job.location
			print("\t" + uu(job_string), file=f)	

	if first_year_experience:
		years_of_experience = datetime.datetime.today().year - first_year_experience
		print("\nYears of experience: " + str(years_of_experience), file=f)

	first_school_year = None
	first_grad_year = None
	age = None
	if client_linkedin_contact.schools:
		print("\nEducation:", file=f)
		for school in client_linkedin_contact.schools:
			school_string = ""
			if school.name: school_string = school_string + school.name + ": " 
			if school.degree: school_string = school_string + school.degree + " " 
			if school.start_date: 
				if not first_school_year or school.start_date.year<first_school_year: first_school_year = school.start_date.year
				school_string = school_string + "(" + str(school.start_date.year) + " - "
				if school.end_date: school_string = school_string + str(school.end_date.year) + ")"
				else: school_string = school_string + "?)"
			elif school.end_date: school_string = school_string + "(? - " + str(school.end_date.year) + ")"
			if school.end_date and (not first_grad_year or school.end_date.year<first_grad_year): first_grad_year = school.end_date.year
			print("\t" + uu(school_string), file=f)			

	if first_school_year: age = datetime.datetime.today().year - first_school_year + 18
	elif first_grad_year: age = datetime.datetime.today().year - first_grad_year + 22
	
	if age: print("\nAge: " + str(age), file=f)

	angellist_url = get_specific_url(social_accounts,'angel.co')
	if angellist_url:
		angelist_info = get_angellist_info(angellist_url)
		print("\nAngel invementment information:", file=f)
		print("\tFollowers: " + str(angelist_info.get("followers")), file=f)
		if angelist_info.get("investments"):
			print("\tInvestments: ", file=f)
			for i in angelist_info.get("investments"):
				string = i.get("company").get("company_name")
				amount = 0
				for k in i.get("investments"):
					a = k.get("amount")
					if a: amount += a
				if amount: string = string + ". Amount: $" + str(amount)
				print("\t\t"+string, file=f)

	f.close()

for name in names:
	directory = "/Users/lauren/Documents/data/" + name
	filename = directory + "/" + name + ".txt" 
	htmlfilename = directory + "/" + name + ".html" 
	otherfilename = directory + "/" + name + "_content.html" 
	f = open(filename,'r')
	html_content = ""
	text = f.readlines()
	links = set()
	usernames = set()
	first_name = name.split(" ")[0].strip().lower()
	last_name = name.split(" ")[-1].strip().lower()
	bad_links = set()
	nonmatching_links = set()
	loggedin_links = set()
	rejected_links = set()
	image_links = set()
	content_links = set()
	for line in text:
		if re.match("\t\S+@\S+\.\S+",line): 
			usernames.add(line.strip().split("@")[0].lower())
		elif re.match("\thttp",line): 
			links.add(line.strip())
	for link in links:
		if get_domain(link) in ['facebook.com','linkedin.com','plus.google.com']: 
			loggedin_links.add(link)
			continue
		try:
			response = requests.get(link, headers=headers)
		except:
			bad_links.add(link)
			continue    		
		if response.status_code in [404,410]: 
			bad_links.add(link)
			continue
		if response.status_code == 200:
			content = response.content
			if content.lower().find("html") == -1 : 
				image_links.add(link)
				continue
			match = False
			if (content.lower().find(first_name) > -1 and content.lower().find(last_name) > -1): match = True
			else:
				for username in usernames:
					if content.lower().find(username) > -1:
						match = True
						break
			if not match: 
				nonmatching_links.add(link)
				continue
			content_links.add(link)
			html_content+=content
		else: rejected_links.add(link)
	all_content = "<!DOCTYPE html><html><body style='font-size: 150%; margin: 20px 20px 20px 20px; '>"
	for image in image_links:
		if image.find('gravatar.com') > -1: continue
		k = '<img src="' + image + '">'
		all_content += k
	for i in loggedin_links:
		k = '<p><a href="' + i + '">' + get_domain(i) + '</a></p>'
		all_content += k
	k = '<p><a href="' + otherfilename + '">' + 'Other web content' + '</a></p>'
	all_content += k		
	for line in text:
		if line=='\n': k = '<p></p>'
		elif line.find('\thttp') >-1: continue
		elif line.find("Links:") >-1: continue
		elif line.find("Images:") >-1: continue
		elif line.find("Social accounts:") >-1: continue		
		elif line.find("\t") == 0: k = '<li>' + line.strip() + '</li>'
		else: k = '<p>' + line.strip()  + '</p>' 
		all_content += k 
	all_content += "</body></html>"
	html = open(htmlfilename,'w')
	print(all_content, file=html)
	html.close()
	html = open(otherfilename,'w')
	print(html_content, file=html)	
	html.close()