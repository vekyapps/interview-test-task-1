from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import logging
from logging import Formatter, FileHandler
import os

import utility

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from database import db_session
from sqlalchemy import exc
import models


# Configure logging
file_handler = FileHandler(os.path.join(basedir, 'logs', 'error.log'))
file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
)
app.logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

# Base.metadata.create_all(bind=engine)
migrate = Migrate(app, db)


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


###################### LOGIC



@app.route('/')
def home():
    return render_template('pages/home.html')


@app.route('/devices', methods=['GET'])
def devices():
    try:
        search = False
        q = request.args.get('q')
        if q:
            search = True

        page = request.args.get('page', type=int, default=1)
        query = models.Device.query.all()

        data = []
        for device in query:
            data.append({
                'id': device.id,
                'name': device.name,
                'code': device.code,
                'description': device.description,
                'date_created': device.date_created,
                'date_updated': device.date_updated,
                'status': device.status
            })
        output = {'success': True, 'data': data}
    except exc.SQLAlchemyError as e:
        app.logger.error('Cannot fetch data from database, error: ' + str(e))
        output = {'success': False, 'msg': 'Cannot fetch data from database!'}

    return jsonify(output)


@app.route('/contents', methods=['GET'])
def contents():
    if request.args.get('device_id') == None:
        return jsonify({'success': False, 'msg': 'Invalid request!'})
    device = request.args.get('device_id')
    try:
        contents = models.Content.query \
            .filter(models.Content.device == device) \
            .all()
        data = []
        for content in contents:
            data.append({
                'id': content.id,
                'name': content.name,
                'description': content.description,
                'date_created': content.date_created,
                'date_updated': content.date_updated,
                'expire_date': content.expire_date,
                'status': content.status
            })
        output = {'success': True, 'data': data}
    except exc.SQLAlchemyError as e:
        app.logger.error('Cannot fetch data from database, error: ' + str(e))
        output = {'success': False, 'msg': 'Cannot fetch data from database!'}

    return jsonify(output)


@app.route('/import', methods=['POST'])
def import_data():
    filepath = os.path.join(basedir, 'uploads')
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

    filepath_devices = os.path.join(filepath, 'devices.csv')
    device_documents = utility.parse_func(
        schema=schema,
        filepath=filepath_devices,
        lookup_indexes=valid_indexes,
        delimiter=delimiter
    )
    if device_documents == False:
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

    filepath_content = os.path.join(filepath, 'content.csv')
    content_documents = utility.parse_func(
        schema=schema,
        filepath=filepath_content,
        lookup_indexes=valid_indexes,
        delimiter=delimiter
    )

    if content_documents == False:
        return jsonify({'success': False, 'msg': 'Invalid configuration provided for parsing content csv file'})

    try:
        for device in device_documents:
            existing_device = db.session.query(models.Device)\
                .filter(models.Device.code == device['code']).\
                first()

            if existing_device:
                device = existing_device
            else:
                device = models.Device(**device)
            db.session.add(device)

        db.session.commit()
        for content in content_documents:
            content = models.Content(**content)
            db.session.add(content)

        db.session.commit()
        output = {'success': True, 'msg': 'Successfully imported!'}
    except AssertionError as e:
        app.logger.error('Data error! Cannot import csv files to database, error: ' + str(e))
        output = {'success': False,
                  'msg': 'There was an error during the operation! Please check CSV files that you are sending.'}
    except exc.SQLAlchemyError as e:
        app.logger.error('Database error! Cannot import csv files to database, error: ' + str(e))
        output = {'success': False, 'msg': 'There was an error during the operation!'}

    return jsonify(output)

@app.route('/folders', methods=['GET'])
def get_folders():
    output = utility.directory_walk(os.path.join(basedir, 'uploads'))
    return jsonify({'success': True, 'data': output})

# Error handlers.
@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)