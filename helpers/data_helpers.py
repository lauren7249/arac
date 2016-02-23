import collections
import itertools
import operator
import numpy as np
from collections import defaultdict

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        if not v and v != 0:
            continue
        if isinstance(v, list):
            continue
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def merge_by_key(d1, d2):
    merged = {}
    for key in set(d1.keys()) & set(d2.keys()):
        merged[key] = d1[key] + d2[key]
    for key in set(d1.keys()) - set(d2.keys()):
        merged[key] = d1[key]     
    for key in set(d2.keys()) - set(d1.keys()):
        merged[key] = d2[key]              
    return merged

def most_common(L):
    # get an iterable of (item, iterable) pairs
    SL = sorted((x, i) for i, x in enumerate(L))
    # print 'SL:', SL
    groups = itertools.groupby(SL, key=operator.itemgetter(0))
    # auxiliary function to get "quality" for an item
    def _auxfun(g):
        item, iterable = g
        count = 0
        min_index = len(L)
        for _, where in iterable:
            count += 1
            min_index = min(min_index, where)
            # print 'item %r, count %r, minind %r' % (item, count, min_index)
        return count, -min_index

def parse_out(text, startTag, endTag):
    """
    Takes a section of text and finds everything between a start tag and end tag
    in html
    """
    region = ""
    region_start = text.find(startTag)
    if region_start > -1:
        region = text[region_start+len(startTag):]
        region_end = region.find(endTag)
        if region_end > -1:
            region = region[:region_end]
    return region
          # pick the highest-count/earliest item
    try:
        return max(groups, key=_auxfun)[0]
    except:
        return None

def get_center(coords, remove_outliers=False):
    """
    We use this to find the center of a bunch of coordinates
    """
    distances = []
    for coord in coords:
        total_distance = 0
        for coord2 in coords:
            total_distance += coord.distance_to(coord2)
        distances.append(total_distance)
    if remove_outliers:
        for i in xrange(len(coords)):
            if distances[i] > np.mean(distances) + np.std(distances):
                coords.remove(coords[i])
    min_total_distance = None
    center = None
    for coord in coords:
        total_distance = 0
        for coord2 in coords:
            total_distance += coord.distance_to(coord2)
        if total_distance<min_total_distance or min_total_distance is None:
            min_total_distance = total_distance
            center = coord
    return center

def json_array_to_matrix(json_array):
    all_keys = defaultdict(int)
    flattened_array = []
    for rec in json_array:
        flattened = flatten(rec)
        flattened_array.append(flattened)
        keys = flattened.keys()
        for key in keys:
            all_keys[key] += 1
    columns = sorted(all_keys, key=all_keys.get, reverse=True)
    #header
    print columns
    matrix = [columns]
    for rec in flattened_array:
        row = []
        for column in columns:
            row.append(rec.get(column))
        matrix.append(row)
    return matrix

        