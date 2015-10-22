import multiprocessing
import threading
from consume.api_consumer import query_vibe
from prime.prospects.models import get_or_create, EmailContact, session

class ProcManager(object):
	def __init__(self):
		self.procs = []
		self.errors_flag = False
		self._threads = []
		self._lock = threading.Lock()

	def terminate_all(self):
		with self._lock:
			for p in self.procs:
				if p.is_alive():
					print "Terminating %s" % p
					p.terminate()

	def launch_proc(self, func, args=(), kwargs= {}):
		t = threading.Thread(target=self._proc_thread_runner,
		                     args=(func, args, kwargs))
		self._threads.append(t)
		t.start()

	def _proc_thread_runner(self, func, args, kwargs):
		p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
		self.procs.append(p)
		p.start()
		while p.exitcode is None:
			p.join()
		if p.exitcode > 0:
			self.errors_flag = True
			self.terminate_all()

	def wait(self):
		for t in self._threads:
			t.join()


def email_contacts_linkedin_urls(unique_emails):
	for_vibe = []
	email_contacts = []
	for email in unique_emails.keys()[500]:
		ec = get_or_create(session,EmailContact,email=email)	
		if ec.linkedin_url:
			continue
		email_contacts.append(ec)
		if not ec.vibe_response or ec.vibe_response.get("statusCode")==1005:
			for_vibe.append(email)

	proc_manager = ProcManager()
	for email in for_vibe:
		proc_manager.launch_proc(query_vibe, args=(email,)) 
	proc_manager.wait()
	if proc_manager.errors_flag:
		print "Vibe api key ran out"
	else:
		print "Everything closed cleanly"			

	for ec in email_contacts:
		