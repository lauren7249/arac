import re
import json

def reformat_schools(educations):
    schools = []
    if not educations:
        return schools
    for education in educations:
        school = {}
        if education.get("degrees"):
            school["degree"] = ", ".join(education.get("degrees"))
        elif education.get("degree") and education.get("major"):
            school["degree"] =  "{}, {}".format(education.get("degree"), education.get("major"))
        elif education.get("degree"):
            school["degree"] = education.get("degree")
        elif education.get("major"):
            school["degree"] = education.get("major")

        school["end_date"] = education.get("end")
        school["college"] = education.get("name")
        school["start_date"] = education.get("start")
        if education.get("profile_url") and education.get("profile_url").split("=")[-1] and education.get("profile_url").split("=")[-1].isdigit():
            school["college_id"] = education.get("profile_url").split("=")[-1]
        school["college_linkedin_url"] = education.get("profile_url")
        school["major"] = education.get("major")
        school["degree_type"] = education.get("degree")
        schools.append(school)
    return schools

def reformat_jobs(jobs):
    experiences = []
    if not jobs:
        return experiences
    for job in jobs:      
        experience = {}
        experience["description"] = job.get("description")
        experience["end_date"] = job.get("end")
        experience["title"] = job.get("title")
        experience["company"] = job.get("organization",[{}])[0].get("name")
        if job.get("organization",[{}])[0].get("profile_url"):
            url =  job.get("organization",[{}])[0].get("profile_url")
            experience["company_linkedin_url"] = url
            if url.split("/")[-1].isdigit():
                experience["company_id"] = url.split("/")[-1]
        experience["start_date"] = job.get("start")
        experience["duration"] = job.get("duration")
        experience["location"] = job.get("location")
        experiences.append(experience)    
    return experiences

def reformat_crawlera(json):
    if not json or not json.keys():
        return {}
    for key in json.keys():
        if json[key] is None: json.pop(key)
    schools = reformat_schools(json.get("education",[]))
    experiences = reformat_jobs(json.get("experience",[]))
    groups = []
    for group in json.get("groups",[]):
        if group.get("profile_url") and group.get("profile_url").split("=")[-1].isdigit():
            group["group_id"] = group.get("profile_url").split("=")[-1]
        group["group_url"] = group.pop("profile_url",None)
        group["image_url"] = group.pop("logo_url",None)
        groups.append(group)
    projects = []
    for p in json.get("projects",[]):
        project = {}
        project["description"] = p.get("description")
        project["title"] = p.get("title")
        project["other_people"] = [member.get("full_name") for member in  p.get("members",[])]
        project["other_people_links"] = [member.get("url") for member in  p.get("members",[])]
        if p.get("date"):
            dates = re.findall("\D*\d{4}",p.get("date"))
            if len(dates) >1:
                project["start_date"] = dates[0].strip()
                project["end_date"] = dates[-1].strip()
            elif len(dates):
                project["start_date"] = dates[0].strip()
                project["end_date"] = dates[0].strip()
        projects.append(project)
    causes = json.get("volunteering",[{}])[0].get("causes")
    return {
        'image': json.get("image_url"),
        'linkedin_id': json.get("linkedin_id"),
        'full_name': json.get("full_name"),
        'headline': json.get("headline"),
        'schools': schools,
        'experiences': experiences,
        'skills': json.get("skills"),
        'people': json.get("also_viewed"),
        'connections': json.get("num_connections"),
        'location': json.get("locality"),
        'industry': json.get("industry"),
        "groups": groups,
        "projects": projects,
        "urls":json.get("also_viewed"),
        "interests": json.get("interests"),
        "causes":causes,
        "organizations":json.get("organizations"),
        "source_url": json.get("url"),
        "family_name": json.get("family_name"),
        "given_name": json.get("given_name"),
        "updated": json.get("updated"),
        "_key": json.get("_key"),
        "websites": json.get("websites"),
        "canonical_url": json.get("canonical_url"),
        "courses": json.get("courses"),
        "languages": json.get("languages"),
        "summary": json.get("summary"),
        "certifications": json.get("certifications"),
        "honors_awards": json.get("honors_awards"),
        "publications": json.get("publications"),
        "recommendations": json.get("recommendations"),
        "volunteering": json.get("volunteering"),
        "patents": json.get("patents")
    }

def test_refactor():
    sample_data_path = "/Users/lauren/Documents/arachnid/prime/tests/fixtures/crawlera_sample.jsonl"
    f = open(sample_data_path,"r")
    lines = f.readlines()
    j = [json.loads(line) for line in lines]
    keynames = set()
    for rec in j:
        ref = reformat_crawlera(rec)
        keynames.update(ref.keys())
    for key in keynames:
        print key

    keynames = set()
    sample_data_path = "/Users/lauren/Documents/arachnid/prime/tests/fixtures/crawlera_sample_companies.jsonl"
    f = open(sample_data_path,"r")
    lines = f.readlines()
    j = [json.loads(line) for line in lines]
    keynames = set()
    for rec in j:
        keynames.update(rec.keys())
    for key in keynames:
        print key

    keynames = set()
    sample_data_path = "/Users/lauren/Documents/arachnid/prime/tests/fixtures/crawlera_sample_schools.jsonl"
    f = open(sample_data_path,"r")
    lines = f.readlines()
    j = [json.loads(line) for line in lines]
    keynames = set()
    for rec in j:
        keynames.update(rec.keys())
    for key in keynames:
        print key
