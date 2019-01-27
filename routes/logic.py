from flask import Blueprint, render_template, current_app
from sqlalchemy import exc
import models

import os
import datetime

import utility

from flask import render_template, request, jsonify
from database import db_session

# Dummy blueprint that holds all routes
main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def home():
    return render_template('pages/home.html')


@main_blueprint.route('/devices', methods=['GET'])
def devices():
    g = utility.request_parse(request)

    try:
        c = utility.query_config(
            g=g,
            model=models.Device,
            logger=current_app.logger
        )
        devices = c['query'].all()
        total = c['total']

        data = []
        for device in devices:
            data.append({
                'id': device.id,
                'name': device.name,
                'code': device.code,
                'description': device.description,
                'date_created': str(device.date_created),
                'date_updated': str(device.date_updated),
                'status': device.status
            })
        output = {'success': True, 'data': data, 'total': total}
    except exc.SQLAlchemyError as e:
        current_app.logger.error('Cannot fetch devices data from database, error: %s' % e)
        output = {'success': False, 'msg': 'Cannot fetch data from database!'}

    return jsonify(output)


@main_blueprint.route('/contents', methods=['GET'])
def contents():
    if request.args.get('device_id') == None:
        return jsonify({'success': False, 'msg': 'Invalid request!'})
    device = request.args.get('device_id')

    g = utility.request_parse(request)

    try:
        base_query = models.Content.query \
            .filter(models.Content.device == device)

        c = utility.query_config(
            g=g,
            model=models.Content,
            logger=current_app.logger,
            base_query=base_query
        )
        contents = c['query'].all()
        total = c['total']

        data = []
        for content in contents:
            data.append({
                'id': content.id,
                'name': content.name,
                'description': content.description,
                'date_created': str(content.date_created),
                'date_updated': str(content.date_updated),
                'expire_date': str(content.expire_date),
                'status': content.status
            })
        output = {'success': True, 'data': data, 'total': total}
    except exc.SQLAlchemyError as e:
        current_app.logger.error('Cannot content data for device_id: %s fetch data from database, error: %s' % (str(device), e))
        output = {'success': False, 'msg': 'Cannot fetch data from database! Database error.'}

    return jsonify(output)


@main_blueprint.route('/import', methods=['POST'])
def import_data():
    filepath = os.path.join(current_app.config.get('BASEDIR'), 'uploads')
    import_source = request.form.get('import_source')
    if not import_source == None:
        import_source = import_source.replace('/', os.sep) # Let's be OS independent! Maybe we switch on Windows server one day :)
        filepath = os.path.join(filepath, import_source)

    delimiter = request.form.get('csv_separator')
    if delimiter == None:
        delimiter = ','

    schema = {
        'id': {
            'type': 'integer',
            'required': True
        },
        'name': {
            'type': 'string',
            'required': True,
            'maxlength': 32
        },
        'description': {
            'type': 'string',
            'required': False
        },
        'code': {
            'type': 'string',
            'required': True,
            'maxlength': 30
        },
        'status': {
            'type': 'string',
            'allowed': ['enabled', 'disabled', 'deleted']
        }
    }

    valid_indexes = {
        0: {
            'name': 'id',
            'convert_function': utility.int_convert
        },
        1: {
            'name': 'name'
        },
        2: {
            'name': 'description'
        },
        3: {
            'name': 'code'
        },
        5: {
            'name': 'status'
        }
    }

    devices_filepath = os.path.join(filepath, 'devices.csv')
    device_documents = utility.parse_func(
        schema=schema,
        filepath=devices_filepath,
        lookup_indexes=valid_indexes,
        delimiter=delimiter,
        logger=current_app.logger
    )
    if device_documents == False:
        current_app.logger.error('Invalid configuration provided for parsing content csv file, filepath: "%s"'
                         % devices_filepath)
        return jsonify({'success': False, 'msg': 'Invalid configuration provided for parsing devices csv file'})

    # content
    schema = {
        'name': {
            'type': 'string',
            'required': True,
            'maxlength': 32
        },
        'description': {
            'type': 'string',
            'required': False
        },
        'device': {
            'type': 'integer',
            'required': True
        },
        'expire_date': {
            'type': 'datetime'
        },
        'status': {
            'type': 'string',
            'allowed': ['enabled', 'disabled', 'deleted']
        }
    }

    valid_indexes = {
        1: {
            'name': 'name'
        },
        2: {
            'name': 'description'
        },
        3: {
            'name': 'device',
            'convert_function': utility.int_convert
        },
        4: {
            'name': 'expire_date',
            'convert_function': utility.date_convert
        },
        5: {
            'name': 'status'
        }
    }

    content_filepath = os.path.join(filepath, 'content.csv')
    content_documents = utility.parse_func(
        schema=schema,
        filepath=content_filepath,
        lookup_indexes=valid_indexes,
        delimiter=delimiter,
        logger=current_app.logger
    )

    if content_documents == False:
        current_app.logger.error('Invalid configuration provided for parsing content csv file, filepath: "%s"'
                         % content_filepath)
        return jsonify({'success': False, 'msg': 'Invalid configuration provided for parsing content csv file'})

    try:
        found_codes = []
        for device in device_documents:
            if device['code'] in found_codes:
                current_app.logger.error('Duplicate code: "%s" was found while parsing content csv file, filepath: "%s"'
                                         % (device['code'], content_filepath))
                continue

            found_codes.append(device['code'])
            existing_device = db_session.query(models.Device)\
                .filter(models.Device.code == device['code']).\
                first()

            if existing_device:
                device = existing_device
                device.date_updated = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
            else:
                device = models.Device(**device)
                current_time = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
                device.date_created = current_time
                device.date_updated = current_time

            db_session.add(device)

        db_session.commit()
        for content in content_documents:
            content = models.Content(**content)
            current_time = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
            content.date_created = current_time
            content.date_updated = current_time
            db_session.add(content)

        db_session.commit()
        output = {'success': True, 'msg': 'Successfully imported!'}
    except AssertionError as e:
        current_app.logger.error('Data error! Cannot import csv files to database, error: ' % str(e))
        output = {'success': False,
                  'msg': 'There was an error during the operation! Please check CSV files that you are sending.'}
    except exc.SQLAlchemyError as e:
        current_app.logger.error('Database error! Cannot import csv files to database, error: %s' % str(e))
        output = {'success': False, 'msg': 'Database error!'}

    return jsonify(output)

@main_blueprint.route('/folders', methods=['GET'])
def get_folders():
    output = utility.directory_walk(os.path.join(current_app.config.get('BASEDIR'), 'uploads'))
    return jsonify({'success': True, 'data': output})