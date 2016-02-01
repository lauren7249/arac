import time
from prime.utils.email import sendgrid_email
import requests
import subprocess

def watch(fn):
    fp = open(fn, 'r')
    stacktrace = []
    inerror = False
    while True:
        new = fp.readline()
        if new:
            if "Traceback" in new:
                inerror = True
            if inerror:
                stacktrace.append(new)
            if "Error" in new:
                yield "\n".join(stacktrace)
                stacktrace = []
                inerror = False

        else:
            time.sleep(0.5)
            response = requests.get("https://prime.advisorconnect.co")
            if response.status_code == 500:
                return "App restarted due to 500 status_code"
            elif response.status_code != 200:
                yield "App gave {} status_code".format(response.status_code)

fn = 'true'
for hit_sentence in watch(fn):
    sendgrid_email("frontend_error@advisorconnect.co", "Front end error", hit_sentence)
subprocess.call("~/prime/restart_app.sh", shell=True)