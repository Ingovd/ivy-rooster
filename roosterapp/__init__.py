import os

from typing import Optional

from urllib.parse import urlparse

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .templates.messages import *
from .sql import Base
from roosterapp.routes import profile_crud, dole_crud, staff_crud, client_crud, session_crud, person_switch, rooster_maker
# from .routes import *


def create_app(config={}):
    if path := config.get('INSTANCE_PATH'):
        app = Flask(__name__, instance_path=path)
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.logger.info(APP_CREATED_FLASK_1PATH.format(app.instance_path))
    app.config.from_pyfile(os.path.join(app.instance_path, 'config.py'))
    app.config.update(config)

    with app.app_context():
        app.db = SQLAlchemy()
        app.db.init_app(app)
        Base.metadata.create_all(bind=app.db.engine)
        app.register_blueprint(profile_crud)
        app.register_blueprint(dole_crud)
        app.register_blueprint(staff_crud)
        app.register_blueprint(client_crud)
        app.register_blueprint(session_crud)
        app.register_blueprint(person_switch)
        app.register_blueprint(rooster_maker)
    return app
