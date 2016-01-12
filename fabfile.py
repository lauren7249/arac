from fabric import colors
import sys
import boto
from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.project import *
import os

env.app = "prime"
env.dest = "~/%(app)s" % env
env.hosts = "10.143.114.147"
env.user = "james"
env.use_ssh_config = True

def reload_gunicorn():
    sudo("pkill -f uwsgi" % env)
    sudo("env/bin/uwsgi prime/production.ini")

def restart_worker():
    sudo("pkill -f python" % env)
    with cd("~/%(app)s"% env):
        run("nohup python worker.py &")

def deploy(branch):
    print(colors.yellow("Deploying sources to %(host)s." % env))
    pull_from_git(branch)
    reload_gunicorn()
    restart_worker()

def pull_from_git(branch):
    with cd("~/%(app)s"% env):
        run("git checkout {}".format(branch))
        run("git pull origin {}".format(branch))

