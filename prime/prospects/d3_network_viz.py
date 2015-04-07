import json, re, simplejson, os, sys
from prime.prospects.models import db, Prospect
from prime.prospects.prospect_list2 import ProspectList
import shutil
from consume.consumer import *

MAX_CUTTOFF = 250
MATCH_CUTTOFF = 0.00

server_folder = "/home/ubuntu/arachnid/prime/dataviz/interactive_network/"
ids = []
current_Persons = []

def id_for(prospect_name, prospect_id):
  id = prospect_name + "_" + str(prospect_id)
  id = re.sub('\s+',"_", id)
  id = re.sub('\W+',"", id).lower()
  ids.append(id)
  return id

def prospect_for(root):
  url = root["url"]
  info = get_info_for_url_live(url)
  prospect = create_prospect_from_info(info, url)
  print prospect.name
  return prospect

def copy_dependencies(id):
  shutil.rmtree(folder_for(id) + "/coffee", ignore_errors=True)
  shutil.copytree(server_folder + "generic/coffee", folder_for(id) + "/coffee")
  shutil.copyfile(server_folder + "generic/index.html", folder_for(id) + "/index.html")

def folder_for(id):
  return server_folder + id

def filename_for(id):
  folder = folder_for(id)
  if not os.path.exists(folder):
    os.makedirs(folder) 
  if not os.path.exists(folder + "/data"):
    os.makedirs(folder + "/data")       
  filename = folder + "/data/nodes.json"  
  return filename

def get_similar(prospect):

  #actually get results
  plist = ProspectList(prospect)
  results = plist.get_results(restrict_to_knowns=True)
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
      Person["connections"] = r["connections"]
      Person["image_url"] = r["image_url"]
      Person["url"] = r["url"]
      Person["s3_key"] = r["s3_key"]
      Person["salary"] = numeric(r["salary"])
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
  all_Persons = [root]

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

def numeric(dollar):
  if dollar is None or len(dollar) == 0: return None
  num = re.sub("[^0-9]","",dollar)
  if num is None or len(num) == 0: return None
  return int(num)

def create_network_viz(search_term, pretty_name):
  info = get_info_for_url_live(search_term)
  prospect = create_prospect_from_info(info, search_term)
  root = {}
  copy_dependencies(pretty_name)
  root["name"] = prospect.name
  root["id"]  = id_for(prospect.name, prospect.id)
  root["filename"] = filename_for(pretty_name)
  root["entity"] = prospect.industry_raw
  root["linkedin_id"] = prospect.linkedin_id
  root["connections"] = prospect.connections
  root["image_url"] = prospect.image_url
  root["url"] = prospect.url
  root["s3_key"] = prospect.s3_key
  root["match"] = 999
  root["salary"] = numeric(prospect.calculate_salary)
  grab(root, root["filename"])

if __name__ == "__main__":
  search_term = sys.argv[1]
  webname = sys.argv[2]
  create_network_viz(search_term, webname)
