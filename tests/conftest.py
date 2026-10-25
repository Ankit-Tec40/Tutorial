import pytest
from app import create_app
from app.extensions import db
from app.lessons.seed_data import seed_database


@pytest.fixture
def app():
    """Configures test application with an in-memory SQLite database."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        seed_database()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the application's Click commands."""
    return app.test_cli_runner()
