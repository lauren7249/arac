import requests
import json

api_key = "53226ed8a4095990a1d715f9c8de93eef9fb83ff94d41c680873ed19875c9a9f"
url = 'https://api.digitalocean.com/v2/droplets'

headers = {'Authorization': "Bearer %s" % api_key,'Content-Type': 'application/json',}

def create_droplet(name='test', region_id='fra1'):
	size_id = '512mb'
	image = '11968976'
	ssh_key_ids = ['cb:75:6a:85:27:f4:7a:4c:22:ce:57:05:7c:3f:8a:2d']
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
	return resp.json()

def delete_droplet(ip):
	null = None
	true = True
	false = False
	resp = requests.get(url, headers=headers)
	d = eval(resp.content)
	droplets = d.get("droplets")
	for droplet in droplets:
		ip_address = droplet.get("networks").get("v4")[0].get("ip_address")
		if ip_address == ip:
			id = droplet.get("id")
			resp = requests.delete(url + "/" + str(id), headers=headers)
			return resp.status_code == 204
	return False