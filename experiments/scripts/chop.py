import csv
import sys
import re
import argparse
from itertools import islice
from contextlib import contextmanager

from py2neo import neo4j, node, rel

from bs4 import BeautifulSoup

csv.field_size_limit(sys.maxsize)

graph_db = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")


def main(filename):
    i = 0

    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=',')

        for row in islice(reader, 1, None):
            row_id, url, html = row
            soup = BeautifulSoup(html)

            result = parse_html(html)
            if result.get('full_name'):
                for school in result.get('schools', []):
                    res = list(graph_db.find('School', property_key='name', property_value=school))
                    if not res:
                        school_node, = graph_db.create(node(name=school))
                        school_node.add_labels('School')
                        print 'Added School', school
                for company in result.get('companies', []):
                    res = list(graph_db.find('Company', property_key='name', property_value=company))
                    if not res:
                        company_node, = graph_db.create(node(name=company))
                        company_node.add_labels('Company')
                        print 'Added Company', company

                res = list(graph_db.find('Person', property_key='url', property_value=url))
                if not res:
                    person_node, = graph_db.create(node(
                        name=result.get('full_name'),
                        url=url
                    ))
                    person_node.add_labels('Person')

                # ok now generate the links
                for person in graph_db.find('Person', property_key='url', property_value=url):
                    for company in result.get('companies', []):
                        companies = list(graph_db.find('Company', property_key='name', property_value=company))
                        for company in companies:
                            graph_db.create( (person, 'WorkedAt', company) )
                    for school in result.get('schools', []):
                        schools = list(graph_db.find('School', property_key='name', property_value=school))
                        for school in schools:
                            graph_db.create( (person, 'WentTo', school) )

            if i % 100 == 0:
                print i, ' ith time'

            i+=1

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
