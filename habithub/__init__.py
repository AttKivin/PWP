import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" \
                                            + os.path.join(app.instance_path, "test.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    from . import models
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.seed_db_command)
    app.cli.add_command(models.check_db_command)

    from . import models
    from . import api
    from .utils import UserConverter, HabitConverter

    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["habit"] = HabitConverter # Still not sure about this,

    app.register_blueprint(api.api_bp)
    return app

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
