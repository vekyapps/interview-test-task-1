from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
import os
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker, validates
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('sqlite:///database.db', echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Configure logging
file_handler = FileHandler(os.path.join(basedir, 'logs', 'error.log'))
file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
)
app.logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

class Device(Base):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.TEXT)
    code = db.Column(db.String(30), unique=True, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    date_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = db.Column(db.Enum('enabled', 'disabled', 'deleted'), nullable=False)

    @validates('name')
    def validate_username(self, key, name):
        if not name:
            raise AssertionError('No name provided')
        if len(name) < 1 or len(name) > 32:
            raise AssertionError('Name can contain max. 32 chars.')

        return name

class Content(Base):
    __tablename__ = 'contents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.TEXT)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"))
    device = db.relationship('Device', backref='content')

    date_created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    date_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    expire_date = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = db.Column(db.Enum('enabled', 'disabled', 'deleted'), nullable=False)

Base.metadata.create_all(bind=engine)

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def home():
    return render_template('pages/home.html')


@app.route('/search', methods=['POST'])
def search():
    try:
        db.session.commit()
        output = {'success': True, 'data': 'Successfully imported!'}
    except exc.SQLAlchemyError as e:
        app.logger.error('Cannot fetch data from database, error: '+str(e))
        output = {'success': False, 'msg': 'Cannot fetch data from database!'}

    return jsonify(output)


@app.route('/import', methods=['POST'])
def import_data():
    devices_file = os.path.join(basedir, 'uploads', 'devices.csv')
    if not os.path.isfile(devices_file) or not os.access(devices_file, os.R_OK):
        return jsonify({'success': True, 'msg': 'Devices file is missing!'})

    content_file = os.path.join(basedir, 'uploads', 'content.csv')
    if not os.path.isfile(content_file) or not os.access(content_file, os.R_OK):
        return jsonify({'success': True, 'msg': 'Content file is missing!'})

    default_separator = app.config.get('DEFAULT_CSV_SEPARATOR')
    if not default_separator:
        default_separator = ","
    with open(devices_file) as f:
        for line in f.readlines():
            line = line.rstrip().rstrip(",")
            attributes = line.split(default_separator)
            row_data = {}
            if attributes[1]:
                row_data['name'] = attributes[1]

            if attributes[2]:
                row_data['description'] = attributes[2]
            try:
                device = Device(**{'name': ''})
            except AssertionError as e:
                pass

    with open(content_file) as f:
        for line in f.readlines():
            line = line.rstrip().rstrip(",")
            attributes = line.split(default_separator)

    try:
        device = Device(**{'name': ''})
        db.session.add(device)
        db.session.commit()
        output = {'success': True, 'msg': 'Successfully imported!'}
    except AssertionError as e:
        app.logger.error('Data error! Cannot import csv files to database, error: '+str(e))
        output = {'success': False, 'msg': 'There was an error during the operation! Please check CSV files that you are sending.'}
    except exc.SQLAlchemyError as e:
        app.logger.error('Database error! Cannot import csv files to database, error: '+str(e))
        output = {'success': False, 'msg': 'There was an error during the operation!'}

    return jsonify(output)


# Error handlers.
@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)