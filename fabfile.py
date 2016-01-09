from fabric import colors
import sys
import boto
from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.project import *
import os

env.app = "prime"
env.dest = "/home/james/%(app)s" % env
env.hosts = "10.143.114.147"
env.user = "james"
env.use_ssh_config = True

def reload_gunicorn():
    sudo("kill -HUP `cat /tmp/uniqueio.pid`" % env)

def deploy():
    print(colors.yellow("Deploying sources to %(host)s." % env))
    pull_from_git()
    cache_bust()
    #migrate()
    reload_supervisor()

def pull_from_git():
    with cd("/home/james/%(app)s"% env):
        run("git fetch origin master")
        run("git merge origin/master --no-edit")


def reload_supervisor():
    sudo("service supervisor restart")

def migrate():
    run(". /home/ubuntu/env/bin/activate")
    with cd("/home/ubuntu/%(app)s" % env):
        run("python manage.py migrate")
