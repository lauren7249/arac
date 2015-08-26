#!/usr/bin/env python
"""
CloudSponge Contact Importer API Python Client
"""

import requests


class CloudSponge:
    """
    Python Client for the CloudSponge Contact Importer API
    """

    base_url = 'https://api.cloudsponge.com'
    urls = {
        "begin_import": "{}/begin_import/user_consent{}",
        "get_events": "{}/events{}",
        "get_contacts": "{}/contacts{}"
    }

    class Services(object):
        yahoo = 'YAHOO'
        gmail = 'GMAIL'
        windowslive = 'WINDOWSLIVE'

    def __init__(self, domain_key, domain_password, api_format='.json'):
        self.credentials = {
            'domain_key': domain_key,
            'domain_password': domain_password
        }
        self.api_format = api_format

    def _get_url(self, urlname, import_id=None):
        """
        Construct cloudsponge api url
        """
        if urlname in self.urls:
            url = self.urls[urlname].format(self.base_url, self.api_format)
            if import_id:
                url = '{}/{}'.format(url, import_id)
        else:
            url = None
        return url

    def begin_import(self, service, opt_include=None,
                     opt_user_id=None, opt_echo=None):
        """
        Call cloudsponge api to get url redirect for user
        to approve email contacts import
        """

        payload = self.credentials
        payload['service'] = service

        url = self._get_url('begin_import')
        r = requests.get(url, params=payload)
        return r.json()

    def get_events(self, import_id):
        """
        Call cloudsponge api to retrieve events
        related to import
        """
        url = self._get_url('get_events', import_id)
        r = requests.get(url, params=self.credentials)
        return r.json()

    def get_events_status(self, import_id):
        """
        Use events to determine general status. Will be
        one of "WORKING", "COMPLETED", or "ERROR"
        """
        resp = self.get_events(import_id)
        for event in resp['events']:
            if event['status'] == 'ERROR':
                return "ERROR"
            if event['event_type'] == 'COMPLETE' and \
                    event['status'] == 'COMPLETED':
                return "COMPLETED"
        return "WORKING"

    def get_contacts(self, import_id):
        """
        Call cloudsponge api to retrieve normalized contact list
        """
        url = self._get_url('get_contacts', import_id)
        r = requests.get(url, params=self.credentials)
        return r.json()
