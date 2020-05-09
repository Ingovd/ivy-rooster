import os

from typing import Optional

from urllib.parse import urlparse

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .templates.messages import *


def create_app(config={}):
    if path := config.get('INSTANCE_PATH'):
        app = Flask(__name__, instance_path=path)
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.logger.info(APP_CREATED_FLASK_1PATH.format(app.instance_path))
    app.config.from_pyfile(os.path.join(app.instance_path, 'config.py'))
    app.config.update(config)

    with app.app_context():
        app.db_backend = SQLAlchemy()
        app.db_backend.init_app(app)
        from roosterapp.routes import rooster_crud
        app.register_blueprint(rooster_crud)
    return app
