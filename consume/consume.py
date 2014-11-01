import argparse
import boto
import logging
import models
import json

from boto.s3.key import Key
from boto.exception import S3ResponseError
from parser import lxml_parse_html
from convert import parse_html

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

s3conn = boto.connect_s3()
bucket = s3conn.get_bucket('arachid-results')

def url_to_key(url):
    return url.replace('/', '')

def get_info_for_url(url):
    key = Key(bucket)
    key.key = url_to_key(url)

    data = json.loads(key.get_contents_as_string())

    #print contents
    info = parse_html(data['content'])

    return info


def info_is_valid(info):
    return info.get('full_name') and \
           info.get('linkedin_id')

def process_from_file(url_file):
    session = models.Session()

    with open(url_file, 'r') as f:
        for url in f:
            url = url.strip()
            try:
                info = get_info_for_url(url)
                print info
                if info_is_valid(info):
                    cleaned_id = info['linkedin_id'].strip()

                    if models.Prospect.linkedin_exists(session, cleaned_id):
                        logger.debug('Already processed linked in id {}'.format(
                            cleaned_id
                        ))
                        continue

                    new_prospect = models.Prospect(
                        url=url,
                        name        = info['full_name'],
                        linkedin_id = cleaned_id,
                        location_raw = info.get('location'),
                        industry_raw = info.get('industry')
                    )

                    session.add(new_prospect)
                    session.flush()

                    for school in info.get('schools', []):
                        new_education = models.Education(
                            user = new_prospect.id,
                            school_raw = school
                        )
                        session.add(new_education)

                    for experience in info.get('experiences', []):
                        new_job = models.Job(
                            user = new_prospect.id,
                            title = experience.get('title'),
                            company_raw = experience.get('company')
                        )
                        session.add(new_job)

                    session.commit()

                    logging.debug('successfully consumed {}'.format(url))

                else:
                    logger.error('could not get valid info for {}'.format(url))

            except S3ResponseError:
                logger.error('couldn\'t get url {} from s3'.format(url))

            break
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url_file')

    args = parser.parse_args()
    process_from_file(args.url_file)

if __name__ == '__main__':
    main()

