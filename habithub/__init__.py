"""
Init file for habithut package. This file contains the function
that creates an application
"""

import os
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flasgger import Swagger
from sqlalchemy.engine import Engine

db = SQLAlchemy()
cache = Cache()

def create_app():
    """
    Create an application and return it based on configuration. It also
    adds command line to the application that can be used from the terminal.
    The package uses converters for different resources and the mapping
    section adds those converters.
    """
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" \
                                            + os.path.join(app.instance_path, "test.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CACHE_TYPE"] = "FileSystemCache"
    app.config["CACHE_DIR"] = os.path.join(app.instance_path, "cache")
    db.init_app(app)
    cache.init_app(app)

    from . import models
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.seed_db_command)
    app.cli.add_command(models.check_db_command)

    from . import api
    from .utils import UserConverter, HabitConverter, ReminderConverter, TrackingConverter
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["habit"] = HabitConverter
    app.url_map.converters["reminder"] = ReminderConverter
    app.url_map.converters["tracking"] = TrackingConverter

    app.register_blueprint(api.api_bp)

    doc_path = os.path.join(os.path.dirname(__file__), "doc", "habithub.yml")
    app.config["SWAGGER"] = {
        "title": "HabitHub API",
        "openapi": "3.0.4",
        "doc_dir": os.path.join(os.path.dirname(__file__), "doc"),
    }
    Swagger(app, template_file=doc_path)

    return app

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
