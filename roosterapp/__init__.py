import os

from typing import Optional

from urllib.parse import urlparse

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .templates.messages import *

from .database.inmemory import InMemoryUrls, InMemoryDB
from .database.sql import SqlUrls


def create_app(config={}):
    if path := config.get('INSTANCE_PATH'):
        app = Flask(__name__, instance_path=path)
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.logger.info(APP_CREATED_FLASK_1PATH.format(app.instance_path))
    app.config.from_pyfile(os.path.join(app.instance_path, 'config.py'))
    app.config.update(config)

    with app.app_context():
        init_database(app)
        init_routes(app)
    return app


def init_database(app):
    app.db_backend = db_backend
    app.urls = url_api


def init_routes(app):
    from yauss.routes import url_crud
    app.register_blueprint(url_crud)
    