from consume.consumer import *
import sys
url = sys.argv[1]
info = get_info_for_url_live(url)
prospect = create_prospect_from_info(info, url)