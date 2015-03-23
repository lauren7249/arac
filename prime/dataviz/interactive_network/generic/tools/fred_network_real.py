import json, re, simplejson, os, sys
from prime.prospects.models import db, Prospect
from prime.prospects.prospect_list2 import ProspectList

MAX_CUTTOFF = 12
MATCH_CUTTOFF = 0.00

server_folder = "/home/ubuntu/arachnid/prime/dataviz/"
ids = []
current_Persons = []
session = db.session

def id_for(prospect_name, prospect_id):
  id = prospect_name + "_" + str(prospect_id)
  id = re.sub('\s+',"_", id)
  id = re.sub('\W+',"", id).lower()
  ids.append(id)
  return id

def prospect_for(root):
  url = root["url"]
  prospect = session.query(Prospect).filter_by(s3_key=url.replace("/", "")).first()
  print prospect.name
  return prospect

def filename_for(id):
  if not os.path.exists(server_folder + id):
    os.makedirs(server_folder + id) 
  if not os.path.exists(server_folder + id + "/data"):
    os.makedirs(server_folder + id + "/data")       
  filename = server_folder + id + "/data/nodes.json"  
  return filename

def get_similar(prospect):

  #actually get results
  plist = ProspectList(prospect)
  results = plist.get_results()
  #print results
  Persons = []
  # puts results.inspect
  for r in results:
    if r["score"] > MATCH_CUTTOFF:
      Person = {}
      Person["match"] = r["score"]
      Person["name"] = r["prospect_name"]
      Person["entity"] = r["current_industry"]
      Person["id"] = id_for(r["prospect_name"],r["id"])
      Person["playcount"] = r["connections"]
      Person["image_url"] = r["image_url"]
      Person["url"] = r["url"]
      Person["s3_key"] = r["s3_key"]
      Persons.append(Person)
      print Person
  return Persons


def links_for(origin, Persons):
  links = []
  for Person in Persons:
    link = {"source" : origin["id"], "target" : Person["id"]}
    reverse_link = {"target" : origin["id"], "source" :Person["id"]}
    if link not in links and reverse_link not in links:
      links.append(link)
  return links

def unseen_Persons(current_Persons, new_Persons):
  unseen = []
  current_Person_ids = []
  for cs in current_Persons:
    current_Person_ids.append(cs["id"])
  for Person in new_Persons:
    if Person["id"] not in current_Person_ids:
      unseen.append(Person)
  return unseen

def expand(Persons, links, root):
  prospect = prospect_for(root)
  new_Persons = get_similar(prospect)
  unseen = unseen_Persons(Persons, new_Persons)[0:MAX_CUTTOFF]
  new_links = links_for(root, unseen)
  return unseen, new_links


def grab(root, output_filename):
  links = []
  all_Persons = []

  first_iteration, new_links = expand(all_Persons, links, root)

  all_Persons = all_Persons + first_iteration
  links = links + new_links

  unlinked_Persons = []

  for Person in first_iteration[1:]:
    new_Persons, new_links = expand(all_Persons, links, Person)
    all_Persons = all_Persons + new_Persons
    unlinked_Persons = unlinked_Persons + new_Persons
    links = links + new_links
    if len(ids)>200: break

  data = {}
  data["nodes"] = all_Persons
  data["links"] = links
  # now write output to a file
  file = open(output_filename, "w")
  # magic happens here to make it pretty-printed
  file.write(simplejson.dumps(data, indent=4))
  file.close()  



if __name__ == "__main__":
  url = sys.argv[0]
  prospect = session.query(Prospect).filter_by(s3_key=url.replace("/", "")).first()
  print prospect.image_url
  root["name"] = prospect.name
  root["id"]  = id_for(prospect.name, prospect.id)
  root["filename"] = filename_for(root["id"])
  root["entity"] = prospect.industry_raw
  root["playcount"] = prospect.connections
  root["image_url"] = prospect.image_url
  root["url"] = prospect.url
  root["s3_key"] = prospect.s3_key
  #print root["id"]
  #print root["filename"]
  grab(root, root["filename"])