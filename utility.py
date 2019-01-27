import os
import csv
import json

from dateutil.parser import parse
from cerberus import Validator

def request_parse(request, show_per_page = 20):
    if not hasattr(request, 'args'):
        return None

    request_config = {}
    valid_args = ['page', 'limit', 'sort', 'query']
    for arg, value in request.args.items():
        if arg in valid_args:
            request_config[arg] = value

    if 'limit' in request_config:
        request_config['limit'] = int(request_config['limit'])
    else:
        request_config['limit'] = show_per_page

    if 'page' in request_config:
        request_config['page'] = int(request_config['page'])

    if 'sort' in request_config:
        request_config['sort'] = json.loads(request_config['sort'])

    if 'query' in request_config:
        request_config['query'] = json.loads(request_config['query'])

    return request_config


def int_convert(value):
    if value.isdigit():
        return int(value)

    return None

def date_convert(value):
    try:
        date = parse(value)
    except ValueError:
        date = None

    return date

def parse_func(**kwargs):
    if ('schema' not in kwargs or
            'lookup_indexes' not in kwargs or
            'filepath' not in kwargs):
        return False

    filepath = kwargs['filepath']
    if (not os.path.isfile(filepath) or
            not os.access(filepath, os.R_OK)):
        return False

    if 'delimiter' in kwargs:
        delimiter = kwargs['delimiter']
    else:
        delimiter = ','

    v = Validator(kwargs['schema'])
    valid_documents = []
    valid_indexes = kwargs['lookup_indexes']
    with open(filepath) as f:
        rows = csv.reader(f, delimiter=delimiter, quoting=csv.QUOTE_ALL)
        for row in rows:
            current_document = {}
            for index, column in enumerate(row):
                if not index in valid_indexes:
                    continue

                column = column.strip()
                if 'convert_function' in valid_indexes[index] and callable(valid_indexes[index]['convert_function']):
                    column = valid_indexes[index]['convert_function'](column)

                current_document[valid_indexes[index]['name']] = column

            if v.validate(current_document):
                valid_documents.append(current_document)
            else:
                # TODO: invalid document
                pass

    return valid_documents

def directory_walk(path):
    directories = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_dir():
                children = directory_walk(path + os.sep + entry.name) # OS independent directory walk
                directories.append({
                    "text": entry.name,
                    "data": children
                })
    return directories