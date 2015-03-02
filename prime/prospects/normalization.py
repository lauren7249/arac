import re

def normalized_degree(degree):
	try:
		degree = re.sub('[^a-zA-Z ]', ' ', degree).lower()
		degree = re.sub(' +',' ',degree)
	except:
		pass
	return degree