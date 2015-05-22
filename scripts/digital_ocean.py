import requests
import json

api_key = "53226ed8a4095990a1d715f9c8de93eef9fb83ff94d41c680873ed19875c9a9f"
url = 'https://api.digitalocean.com/v2/droplets'
headers = {'Authorization': "Bearer %s" % api_key,'Content-Type': 'application/json',}
name = 'test'
size_id = '512mb'
image = '11968976'
region_id = 'fra1'
ssh_key_ids = ['810467']
params = {
        'name': name,
        'size': size_id,
        'image': image,
        'region': region_id,
        'virtio': False,
        'private_networking': False,
        'backups_enabled': False,
}
if ssh_key_ids:
    params['ssh_keys'] = ssh_key_ids

resp = requests.post(url, data=json.dumps(params), headers=headers, timeout=60)
from pprint import pprint
pprint(resp.json())
