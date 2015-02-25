import elasticsearch
from elasticsearch import helpers
import argparse
import csv
import json

ELASTIC_SEARCH_URL = "http://41eb5e9da34f4d3c874fba6842fe3bd7-us-east-1.foundcluster.com:9200"


class SearchIndexer(object):

    def __init__(self, filename, index_name, *args, **kwargs):
        self.file = open(filename, "r")
        self.index_name = index_name
        self.es = elasticsearch.Elasticsearch(ELASTIC_SEARCH_URL)

    def create_mapping(self):
        mapping = {
                "{}".format(self.index_name[:-1]): {
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "item_count": {"type": "integer"}
                        }
                    }
                }
        self.es.indices.create(self.index_name)
        self.es.indices.put_mapping(index=self.index_name, doc_type=self.index_name[:-1], body=mapping)

    def index(self):
        total_count = 0
        count = 0
        items = []
        self.create_mapping()
        for line in csv.reader(self.file, delimiter='\t'):
            try:
                item_count = int(line[2])
            except Exception, e:
                item_count = 0
                print "Error:{}".format(e)

            if item_count > 1:
                item = {
                        "_id": line[0],
                        "_index": self.index_name,
                        "_type": self.index_name[:-1],
                        "_source": {
                            "name": line[1],
                            "item_count": line[2]
                            }
                        }
                items.append(item)
                count += 1
            total_count += 1
            if (count % 10000 == 0):
                helpers.bulk(self.es, items)
                items = []
                print count, total_count
        if len(items) > 0:
            helpers.bulk(self.es, items)
        return True

class SearchRequest(object):

    def __init__(self, query, type='schools', *args, **kwargs):
        self.es = elasticsearch.Elasticsearch(ELASTIC_SEARCH_URL)
        self.query = query
        self.type = type

    def search(self):
        query = {"query":
                    {"term":
                        {"name": "{}".format(self.query.lower())}
                    },
                "size": 100
                }
        results = self.es.search(self.type, \
                q="name:{}".format(self.query.lower()) \
                , size=100).get("hits").get("hits")
        results = sorted(results, key=lambda x: int(x.get("_source")\
                .get("item_count")), reverse=True)
        return [{"id": a.get("_id"),"name": a.get("_source").get("name"), \
                "count": a.get("_source").get("item_count")} for a in
                results[:20]]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('index_name')

    args = parser.parse_args()

    search = SearchIndexer(args.filename, args.index_name)
    search.index()
