import os
import tempfile 
import pytest
from habithub import create_app, db as _db, cache as _cache
from habithub.auth import API_KEY

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True
    app.config["CACHE_TYPE"] = "SimpleCache"

    with app.app_context():
        _db.create_all()
        yield app
        _cache.clear()
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Return a test client that sends the API key header with every request."""
    client = app.test_client()
    client.environ_base["HTTP_X_API_KEY"] = API_KEY
    return client
