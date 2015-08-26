#!/usr/bin/env python

import argparse
from ConfigParser import ConfigParser
import time
import sys
from consume.convert import uu
from cloudsponge import CloudSponge


def main(service):
    ## read config file for credentials
    cp = ConfigParser()
    cp.read('cloudsponge/cloudsponge.conf')
    credentials = dict(cp.items('Credentials'))

    client = CloudSponge(credentials['domain_key'],
                         credentials['domain_password'])

    # initiate import, get redirect url
    resp = client.begin_import(service)
    import_id = resp['import_id']

    # wait for user to approve
    print 'import_id: {}'.format(import_id)
    print '      url: {}'.format(resp['url'])
    raw_input('Go to the url in your browser and grant permission. '
              'Press Enter when ready.')

    # poll until import success or error
    status = "WORKING"
    while status == "WORKING":
        status = client.get_events_status(import_id)
        time.sleep(1)

    # print results
    #if success:
    if status == "COMPLETED":
        resp = client.get_contacts(import_id)
        for contact in resp['contacts']:
            print '{} {}'.format(uu(contact['first_name']),
                                 uu(contact['last_name']))
            for email in contact['email']:
                print '    {}'.format(email['address'])
    else:
        print 'ERROR status detected'


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = argparse.ArgumentParser(
        description='Test CloudSponge import client.')
    parser.add_argument('service', choices=['yahoo', 'gmail', 'windowslive'])
    args = parser.parse_args(sys.argv[1:])
    main(args.service.upper())
