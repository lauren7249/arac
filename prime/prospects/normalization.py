import re

def normalized_degree(degree):
	try:
		degree = re.sub('[^a-zA-Z ]', ' ', degree).lower()
		degree = re.sub(' +',' ',degree)
	except:
		pass
	return degree

def normalized_location(location):
	try:
		location = re.sub('[^a-zA-Z ]', ' ', location).lower()
		location = re.sub(' +',' ',location)
	except:
		pass
	return location	