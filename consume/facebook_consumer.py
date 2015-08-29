import lxml.html
from prime.prospects.get_prospect import session
import re

def parse_facebook_html(source):
    if source is None: return None
    raw_html = lxml.html.fromstring(source)
    article = None
    profile = {} 
    try:
        profile["image_url"] = raw_html.xpath(".//img[@class='profilePic img']")[0].get("src")
    except: 
        pass
    try:
        profile["name"] = raw_html.xpath(".//span[@id='fb-timeline-cover-name']")[0].text
    except: 
        pass       
    try:     
        article = raw_html.xpath(".//div[@role='article']")[0]
    except:
        pass
    if not article: return profile
    for element in article.xpath(".//li/div/div/div/div"):
        text = element.text_content()
        if not text: continue
        if text.find("Lives in ") > -1:
            profile["lives_in"] = text.split("Lives in ")[1]
            continue
        if re.search("[0-9] friends", text) and not profile.get("friend_count"):
            profile["friend_count"] = int(text.split(" friends")[0].replace(',',''))
            continue   
        if text.find("Married") == 0:
            profile["married"] = True    
            if text.find("Married to ") > -1:
                profile["married_to"] = text.split("Married to ")[1].split("\n")[0]
                if text.find("\n") > -1 and text.find("Since "):
                    profile["married_since"] = text.split("\n")[1].split("Since ")[1]
                continue 
        if text.find(" at ") > -1:
            school_info = None
            if text.find("Studies ") == 0:
                school_info = text.split("Studies")[1]
            elif text.find("Studied ") == 0:
                school_info = text.split("Studied")[1]
            if school_info:
                profile["school_major"] = school_info.split(" at ")[0].strip()
                if school_info.find(" at ") > -1: 
                    profile["school_name"] = school_info.split("\n")[0].split(" at ")[1].strip()
                if school_info.find("\n") > -1:
                    dates = school_info.split("\n")[1]
                    if dates: 
                        years = re.findall("\d\d\d\d", dates)
                        if len(years) == 1: 
                            if re.search("^"+years[0],dates): profile["school_start_year"] = int(years[0])
                            elif re.search(years[0]+"$",dates): profile["school_end_year"] = int(years[0])
                        elif len(years) >1:
                            profile["school_start_year"] = int(years[0])
                            profile["school_end_year"] = int(years[1])
                continue
            profile["job_title"] = text.split(" at ")[0]
            profile["job_company"] = text.split("\n")[0].split(" at ")[1]
            if text.find("\n") > -1:
                dates = text.split("\n")[1]
                if dates: 
                    years = re.findall("\d\d\d\d", dates)
                    if len(years) == 1: 
                        if re.search("^"+years[0],dates): profile["job_start_year"] = int(years[0])
                        elif re.search(years[0]+"$",dates): profile["job_end_year"] = int(years[0])
                    elif len(years) >1:
                        profile["job_start_year"] = int(years[0])
                        profile["job_end_year"] = int(years[1])  
            continue
        if text.find("Born on ") > -1:
            profile["dob"] = text.split("Born on ")[1]
        if text.find("From ") > -1:
            profile["from"] = text.split("From ")[1].split("\n")[0]
            continue              
    return profile   

def parse_likers(source):
    likers = []
    try: raw_html = lxml.html.fromstring(source)
    except: return likers
    for element in raw_html.xpath(".//li[@class='fbProfileBrowserListItem']"):
        href = element.find(".//a").get("href")
        username = href_to_username(href)
        likers.append(username)
    return likers

def parse_facebook_engagers(source):
    engagers = {}
    try: raw_html = lxml.html.fromstring(source)
    except: return engagers
    newsfeeds = raw_html.xpath(".//div[@class='fbTimelineCapsule clearfix']")
    commenters = set()
    posters = set()
    like_links = {}
    for newsfeed in newsfeeds:
    	commenter_elements = newsfeed.xpath(".//a[@class=' UFICommentActorName']")
        for element in commenter_elements:
	        href = element.get("href")
	        username = href_to_username(href)
	        commenters.add(username)
    	    
    	poster_elements = newsfeed.xpath(".//div[contains(@class,'userContentWrapper')]")
        for element in poster_elements:
	        try:
	            username = href_to_username(element.xpath(".//div/h5/div/span/a[contains(@href,'https://www.facebook.com')]")[0].get("href"))
	        except: continue
	        posters.add(username)
        likes_elements = newsfeed.xpath(".//a[contains(@href,'browse/likes')]")
        for element in likes_elements:
            href = element.get("href")
            like_links.update({href: []})
    if len(posters): engagers["posters"] = list(posters) 	
    if len(commenters): engagers["commenters"] = list(commenters)
    if len(like_links): engagers["like_links"] = like_links
    return engagers

def parse_facebook_friends(source):
    raw_html = lxml.html.fromstring(source)
    all_elements = raw_html.xpath("//div/div/div/div/div/div/ul/li/div")
    friends = []
    for person in all_elements:
        try:
            profile = person.xpath(".//*[@class='uiProfileBlockContent']")
            if len(profile) ==0: continue
            href = profile[0].find(".//a").get("href")
            username = href_to_username(href)
            friends.append(username)
        except:
            username = None
            continue    	
    return friends

def href_to_username(href):
    username = href.split("/")[-1].split("?")[0]
    if username == "profile.php":
        username = href.split("/")[-1].split("?")[1].split("=")[1].split("&")[0]    
    return username    