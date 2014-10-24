from boto import ec2
from fabric.api import env, run, sudo

env.user = 'ubuntu'
env.parallel = True
env.hosts = []

bad_hosts = []
good_hosts = []

def get_all():
    conn = ec2.connect_to_region('us-east-1')

    instances = conn.get_only_instances()
    env.hosts = [instance.ip_address for instance in instances]

def get_bad():
    tailed = run("tail -n 50 /var/log/supervisor/scraper-0")

    if "raise Phantom" in tailed:
        print 'Bad host detected', env.host

    else:
        print 'Host is ok', env.host


def update():
    get_all()
    run("cd /home/ubuntu/arachnid")
    run("git pull origin feature/onlyredis")
    run("sudo service supervisor restart")
    print "Done", env.host
