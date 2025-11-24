import pytest
from .. import create_app
from ..extensions import db


@pytest.fixture
def app():
    """Flask app configured for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client (simulates HTTP calls)."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Ensure empty tables before each test."""
    from ..extensions import db
    from ..models import User, OwnedCard, WantedCard, Card

    db.session.commit()
    for table in (User, OwnedCard, WantedCard, Card):
        db.session.query(table).delete()
    db.session.commit()
