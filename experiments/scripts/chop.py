import csv
import sys
import re
import argparse
from itertools import islice
from contextlib import contextmanager

from bs4 import BeautifulSoup

csv.field_size_limit(sys.maxsize)

def main(filename):
    i = 0

    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=',')

        for row in islice(reader, 1, None):
            row_id, url, html = row
            soup = BeautifulSoup(html)

            result = parse_html(html)
            if result.get('full_name') == 'James Johnson':
                print result
            if 'Yale University' in result.get('schools', []):
                print result

def first_or_none(l):
    result = l[0] if l else None
    if result:
        return result

def remove_dups(l):
    return list(set(l))

def parse_html(html, debug = False):
    soup = BeautifulSoup(html)

    full_name = None
    full_name_el = first_or_none(soup.find_all(class_='full-name'))
    if full_name_el:
        full_name = full_name_el.text.strip()

    schools = []

    #for l in soup.find_all('a'):
    #    print l

    school_els = soup.find_all(href=re.compile('.edu.'), title="More details for this school")
    if not school_els:
        school_els = soup.find_all(href=re.compile('.edu.'))
    if school_els:
        schools = remove_dups([el.text.strip() for el in school_els if el.text])

    companies = []
    company_els = soup.find_all(class_='company-profile-public')
    if company_els:
        companies += [el.text.strip() for el in company_els if el.text]
    company_els = soup.find_all(href=re.compile('.company.'))
    if company_els:
        companies += [el.text.strip() for el in company_els if el.text]

    companies = remove_dups(companies)

    return {
        'full_name': full_name,
        'schools': schools,
        'companies': companies
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')

    args = parser.parse_args()

    main(args.file)
