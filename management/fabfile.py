from boto import ec2
from fabric import colors
from fabric.api import *
from fabric.contrib.project import *

env.user = 'ubuntu'
env.parallel = True
env.hosts = []

bad_hosts = []
good_hosts = []

def get_all():
    conn = ec2.connect_to_region('us-east-1')

    instances = conn.get_only_instances()
    env.hosts = [instance.ip_address for instance in instances if\
            instance.ip_address]

def get_bad():
    tailed = run("tail -n 50 /var/log/supervisor/scraper-0")

    if "raise Phantom" in tailed:
        print 'Bad host detected', env.host

    else:
        print 'Host is ok', env.host

def get_tail():
    tailed = run("tail -n 10 /var/log/supervisor/scraper-0")


def update():
    with cd("/home/ubuntu/arachnid"):
        run("git add .")
        run("git commit -m 'new updates local'")
        run("git push origin feature/onlyredis")
        run("git pull origin feature/onlyredis")
        sudo("service supervisor restart")
    print "Done", env.host

def update_supervisor():
    with cd("/home/ubuntu/arachnid"):
        run("git pull origin feature/onlyredis")
    with cd("/etc/supervisor/conf.d/"):
        sudo("cp /home/ubuntu/arachnid/conf/scraper.conf /etc/supervisor/conf.d/scraper.conf")
        sudo("service supervisor restart")

