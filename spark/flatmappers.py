import json
from prime.processing_service.helper import name_match
import re
'''
flatmap functions return a list of key, value pairs. this list gets flattened to an rdd of key, value pairs when flatmap is called
'''

def load_people(line):
    linkedin_data = json.loads(line)
    _key = linkedin_data.get("_key")[2:]
    linkedin_id = linkedin_data.get("linkedin_id")
    if _key:
        data_column = [(_key, [_key,"linkedin",   "linkedin_data",       line])]
        if linkedin_id:
            return data_column + [(_key, [_key,"linkedin",   "linkedin_id",       linkedin_id])] 
                #key           #key again   #col.family   #col.name    #col.value
        return data_column
    return []

def load_url_xwalk(line):
    linkedin_data = json.loads(line)
    _key = linkedin_data.get("_key")[2:]
    url = linkedin_data.get("url")
    linkedin_id = linkedin_data.get("linkedin_id")
    if not _key or not url:
        return []
    data_column = [(url, [url, "keys","_key",_key])]
    if linkedin_id:
        return data_column + [(url, [url, "keys","linkedin_id",linkedin_id])]
             #key  #key again   #col.family   #col.name    #col.value
    return data_column

def load_linkedin_id_xwalk(line):
    linkedin_data = json.loads(line)
    _key = linkedin_data.get("_key")[2:]
    linkedin_id = linkedin_data.get("linkedin_id")
    url = linkedin_data.get("url")
    if not _key or not linkedin_id:
        return []
    data_column = [(linkedin_id, [linkedin_id, "keys","_key",_key])]
    if url:
        return data_column + [(linkedin_id, [linkedin_id, "keys","url",url])]
             #key  #key again   #col.family   #col.name    #col.value
    return data_column

def load_by_dob(rec):
    dob = rec[0]
    keys = rec[1][0]
    confidences = rec[1][1]
    return [(name, [name, "matches","keys",json.dumps(keys)]), (name, [name, "matches","confidences",json.dumps(confidences)])]

def load_by_name(rec):
    name = rec[0]
    keys = rec[1][0]
    positions = rec[1][1]
    return [(name, [name, "matches","keys",json.dumps(keys)]), (name, [name, "matches","positions",json.dumps(positions)])]

def parse_names(line):
    linkedin_data = json.loads(line)
    _key = linkedin_data.get("_key")[2:]
    name = linkedin_data.get("full_name")
    if not name:
        return []
    name = re.sub("[^a-z ]","", name.lower().strip())
    name_words = name.split(" ")
    output = []
    for position in xrange(0, len(name_words)):
        name_part = name_words[position]
        row = (name_part, ([_key], [position]))
        output.append(row)
    return output


'''
this section needs to be changed to take into account the fact that there will no longer be linkedin ids
'''
#flatmap
def load_graph(rec):
    linkedin_id = rec[0]
    arr = rec[1]
    urls = [e for e in arr if not e.isdigit()]
    linkedin_ids = [e for e in arr if e.isdigit()]
    return [(linkedin_id, [linkedin_id,"extended","urls",json.dumps(urls)]), (linkedin_id, [linkedin_id,"extended","linkedin_ids",json.dumps(linkedin_ids)])]

#flatmap
def map_also_viewed(line):
    linkedin_data = json.loads(line)
    also_viewed = linkedin_data.get("also_viewed")
    linkedin_id = linkedin_data.get("linkedin_id")
    name = linkedin_data.get("full_name")
    if not also_viewed or not linkedin_id or not name:
        return []
    urls = []    
    for url in also_viewed:
        _name = re.search('http://www.linkedin.com/[^/]+/[^/]+(?=/*)',url)
        if _name:
            _name = _name.group(0).split("/")[-1].replace("-"," ").lower()
            _name = re.sub('[^a-z\s]','',_name)
            if name_match(name, _name): continue         
        urls.append(url)
    #we already have the linkedin id of the current person, so expose the url of the other person as a key to merge with the xwalk and get a linkedin_id
    results =  [(url, linkedin_id) for url in urls]    
    return results

#flatmap
def create_edges(rec):
    #input will look  like (url2, (linkedin_id1, xwalk2))
    url2 = rec[0]
    linkedin_id1 = rec[1][0]
    xwalk2 = rec[1][1]
    linkedin_id2 = json.loads(xwalk2).get("value")
    #we couldnt find the url in the database, so just keep the url and we will handle it in load_graph
    if linkedin_id2 is None:
        linkedin_id2 = url2
    return [(linkedin_id1, linkedin_id2), (linkedin_id2, linkedin_id1)]




