import pytest
from ..extensions import db
from ..models import User, OwnedCard, WantedCard, Card, Set


@pytest.fixture
def app(monkeypatch, tmp_path):
    """
    Create a Flask app wired to a temporary SQLite DB for this test session.
    Ensures we are NOT hitting your real Postgres / seeded data.
    """
    # Temporary SQLite file for the test run
    test_db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

    # Import create_app AFTER we set DATABASE_URL
    from .. import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client (simulates HTTP calls)."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """
    Ensure empty tables before each test.

    This wipes out any seeded/demo data (cards, sets, users, owned, wanted)
    so tests always see a clean database.
    """
    with app.app_context():
        # Delete in an order that won't violate FKs
        for model in (OwnedCard, WantedCard, Card, User, Set):
            db.session.query(model).delete()
        db.session.commit()
