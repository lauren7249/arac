import re
from difflib import SequenceMatcher
import logging
from itertools import izip, cycle
from random import choice
from string import ascii_uppercase
import shlex
import os

logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def uu(str):
    if str:
        try:
            return str.decode("ascii", "ignore").encode("utf-8")
        except:
            return str.encode('UTF-8')
    return None

def get_domain(website):
    if website is None:
        return None
    website = website.lower().replace("https://","").replace("http://","").replace("www.","")
    domain = website.split("/")[0]
    return domain

def domain_match(website1,website2):
    return website1 and website2 and get_domain(website2) == get_domain(website1)

def name_match(name1, name2, intersect_threshold=5):
    name1 = re.sub('[^0-9a-z\s]','',name1.lower())
    name2 = re.sub('[^0-9a-z\s]','',name2.lower())
    if name1 and name2 and name1 == name2:
        return True
    if len(name1) < 3 or len(name2) < 3:
        return False
    name1_words = set(name1.split(" "))
    name2_words = set(name2.split(" "))
    stop_words = ["the", "of","and","a","the","at","for","in","on","school","","inc","llc","co","university","college"]
    for stop_word in stop_words:
        if stop_word in name1_words: name1_words.remove(stop_word)
        if stop_word in name2_words: name2_words.remove(stop_word)
    intersect = name1_words & name2_words
    intersect_threshold = min(intersect_threshold, len(name1_words))
    intersect_threshold = min(intersect_threshold, len(name2_words))
    if len(intersect)>=intersect_threshold: 
        logger.info("Name match: %s == %s", name1, name2)
        return True
    ratio = SequenceMatcher(None, name1, name2).ratio()
    if ratio>=0.8: 
        logger.info("Name match: %s == %s", name1, name2)
        return True
    return False

def get_firstname(str):
    if not str:
        return str
    str = re.sub(" - "," ",str)
    str = re.sub("[^a-zA-Z-]"," ",str)
    str = re.sub("\s+"," ",str.lower().strip())
    firstname = str.split(" ")[0]
    if firstname in ["ms","mr","miss","mrs","dr", "rev", "reverend","professor","prof","md"] and len(str.split(" "))>1: firstname =  str.split(" ")[1]
    return firstname

def resolve_email(email):
    email = email.lower().strip()
    email = email.split("@")[0].replace('.','') + "@" + email.split("@")[-1]
    return re.sub('\+[^@]+(?=@)','', email)

def domestic_area(phone):
    if not phone:
        return None
    phone = re.sub("[^0-9]+"," ",phone).strip()
    if not phone:
        return None
    phone_chunks = phone.split(" ")
    if len(phone_chunks) in [1, 2]:
        if len(phone_chunks[0])==10:
            area_code = phone_chunks[0][:3]
        elif len(phone_chunks[0]) == 11 and phone_chunks[0][:1] == '1':
            area_code = phone_chunks[0][1:4]
        else:
            return None
    #first chunk is not an area code
    elif len(phone_chunks[0]) != 3:
        #not in america
        if phone_chunks[0] != '1':
            return None
        if len(phone_chunks) < 4:
            return None
        area_code = phone_chunks[1]
    #first chunk could be an area code
    else:
        if len(phone_chunks) < 3:
            return None
        area_code = phone_chunks[0]
    if len(area_code) != 3:
        return None
    return area_code


def xor_crypt_string(plaintext, key):
    ciphertext = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(plaintext, cycle(key)))
    return ciphertext.encode('hex')

def xor_decrypt_string(ciphertext, key):
    ciphertext = ciphertext.decode('hex')
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(ciphertext, cycle(key)))

def random_string(length=12):
    return ''.join(choice(ascii_uppercase) for i in range(length))

def csv_line_to_list(line):
    splitter = shlex.shlex(line, posix=True)
    splitter.whitespace = ","
    splitter.whitespace_split=True
    return list(splitter)
