import os
from logging import Formatter, FileHandler, INFO, ERROR

from flask import Flask, render_template
from config import BASEDIR
from database import db_session

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    import models
    models.db.init_app(app)
    models.migrate.init_app(app, models.db)

    @app.teardown_request
    def shutdown_session(exception=None):
        db_session.remove()

    # Error handlers.
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    from routes import logic
    app.register_blueprint(logic.main_blueprint)
    logging_configure(app)
    return app

def logging_configure(app):
    error_file_handler = FileHandler(os.path.join(BASEDIR, 'logs', 'error.log'))
    error_file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )

    logs_file_handler = FileHandler(os.path.join(BASEDIR, 'logs', 'logs.log'))
    logs_file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )

    app.logger.setLevel(INFO)
    error_file_handler.setLevel(INFO)
    logs_file_handler.setLevel(ERROR)
    app.logger.addHandler(error_file_handler)
    app.logger.addHandler(logs_file_handler)

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)