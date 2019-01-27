import os
import csv
import json

from dateutil.parser import parse
from cerberus import Validator


def request_parse(request, show_per_page=20):
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


def query_config(**kwargs):
    model = kwargs['model']
    logger = kwargs['logger']

    table = getattr(model, '__table__')
    cols = [x.name for x in getattr(table, 'columns')]

    if 'base_query' in kwargs:
        base_query = kwargs['base_query']
    else:
        base_query = model.query

    total = base_query
    query = base_query
    g = kwargs['g']
    if 'query' in g:
        query_properties = g['query']
        for property, value in query_properties.items():
            if len(value) == 0:
                continue
            if property in cols:
                query = query.filter(getattr(model, property).like("%s%%%%" % value))
            else:
                if property == 'created_from':
                    query = query.filter(model.date_created >= value)
                if property == 'created_to':
                    query = query.filter(model.date_created <= value)
                if property == 'updated_from':
                    query = query.filter(model.date_updated >= value)
                if property == 'updated_to':
                    query = query.filter(model.date_updated <= value)

    if 'sort' in g:
        sort_properties = g['sort']
        for item in sort_properties:
            if item['property'] not in cols:
                logger.warning('Query ordering by unknown column: "%s"' % item['property'])
                break
            if (item['direction']).lower() == 'asc':
                query = query.order_by(getattr(model, item['property']).asc())
            else:
                query = query.order_by(getattr(model, item['property']).desc())

    query = query.offset((g['page'] - 1) * g['limit']) \
        .limit(g['limit'])

    return {'query': query, 'total': total.count()}

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
            'filepath' not in kwargs or
            'logger' not in kwargs):
        return False

    filepath = kwargs['filepath']
    logger = kwargs['logger']
    if (not os.path.isfile(filepath) or
            not os.access(filepath, os.R_OK)):
        logger.error('Filepath: "%s" does not exists or not accessible!' % filepath)
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

            # Row based cleaning and parsing
            for index, column in enumerate(row):
                if index not in valid_indexes:
                    continue

                column = column.strip()
                if 'convert_function' in valid_indexes[index] and callable(valid_indexes[index]['convert_function']):
                    column = valid_indexes[index]['convert_function'](column)

                current_document[valid_indexes[index]['name']] = column

            # Validation
            if v.validate(current_document):
                logger.info('Valid row data: "%s" , filepath: "%s"!'
                            % (str(current_document), filepath))
                valid_documents.append(current_document)
            else:
                logger.error('Invalid row data: "%s" , errors: "%s", filepath: "%s"!'
                             % (str(current_document), str(v.errors), filepath))

    return valid_documents


def directory_walk(path, logger=None):
    directories = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir():
                    children = directory_walk(path + os.sep + entry.name)  # OS independent directory walk
                    directories.append({
                        "text": entry.name,
                        "data": children
                    })
                else:
                    directories.append({
                        "text": entry.name,
                        "leaf": True
                    })
    except OSError as e:  # Scandir may throw os related error(s)
        if logger:
            logger.error('Cannot read directory content! Error: %s' % e)

    return directories