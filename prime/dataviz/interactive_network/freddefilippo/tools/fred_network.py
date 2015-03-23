import json, re, simplejson

MAX_CUTTOFF = 12
MATCH_CUTTOFF = 0.07

ids = []
current_Persons = []

def id_for(Person):
  id = Person["name"] + "_" + Person["entity"]
  id = re.sub('\s+',"_", id)
  id = re.sub('\W+',"", id).lower()
  ids.append(id)
  return id


def get_similar(old_Person):
  #actually get results
  results = ["Mike"]

  Persons = []
  # puts results.inspect
  for r in results:
    Person = {}
    Person["match"] = 0.5
    Person["name"] = "name"
    Person["entity"] = "entity"
    Person["id"] = id_for(Person)
    Person["playcount"] = 10
    Persons.append(Person)
  
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
  new_Persons = get_similar(root)
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


  data = {}
  data["nodes"] = all_Persons
  data["links"] = links
  # now write output to a file
  file = open(output_filename, "w")
# magic happens here to make it pretty-printed
  file.write(simplejson.dumps(data, indent=4))
  file.close()  



if __name__ == "__main__":
  roots = [
    {"name":"fred", "entity":"Fred DeFilippo", "filename":"fred.json"}
  ]
  for root in roots:
    root["id"]  = id_for(root)

    grab(root, root["filename"])