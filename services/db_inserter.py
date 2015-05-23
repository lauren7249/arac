import web
from prime.utils.update_database_from_dict import *
from prime.prospects.get_prospect import get_session

session = get_session()

urls = (
    '/insert', 'insert'
)

class insert:
    def POST(self):
    	data = web.data()
    	info = eval(data)
    	new_prospect = insert_linkedin_profile(info, session)
    	return new_prospect.id

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()