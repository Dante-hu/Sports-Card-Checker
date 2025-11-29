import pytest
from ..extensions import db
from ..models import User, OwnedCard, WantedCard, Card


@pytest.fixture
def app(monkeypatch, tmp_path):

    # Create a temporary SQLite file for this test session
    test_db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

    # Import create_app *after* DATABASE_URL is patched
    from .. import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client (simulates HTTP calls)."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Ensure empty tables before each test."""
    db.session
