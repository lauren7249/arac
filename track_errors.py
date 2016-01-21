import time
from prime.utils.email import sendgrid_email

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

fn = 'true'
for hit_sentence in watch(fn):
    sendgrid_email("frontend_error@advisorconnect.co", "Front end error", hit_sentence)