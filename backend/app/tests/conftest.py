"""
conftest.py — Test Infrastructure

Design principles (Team standards):
- Each test function gets a FRESH, isolated database (no shared state)
- No hardcoded emails (uuid4-based to prevent UNIQUE violations)
- Transactions are rolled back after each test (no cleanup needed)
- App dependency overrides are set once per session and torn down cleanly
"""
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ─── Path setup ─────────────────────────────────────────────────────────────

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Use in-memory SQLite per test session — fastest and fully isolated
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# ─── Database engine ─────────────────────────────────────────────────────────

from app.db import Base
import app.models  # Register all ORM models

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
# Use a single connection for all tests to share in-memory DB
_connection = _test_engine.connect()
_TestSession = sessionmaker(bind=_connection)


# ─── Schema ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def create_schema():
    """Create all tables once for the session."""
    Base.metadata.create_all(bind=_connection)
    yield
    Base.metadata.drop_all(bind=_connection)


# ─── DB Fixture (per test, uses nested transaction for rollback) ──────────────

@pytest.fixture(name="db")
def db_fixture(create_schema):
    """
    Provide a transactional database session.
    Changes are rolled back after each test — no data leaks between tests.
    """
    transaction = _connection.begin_nested()
    session = _TestSession(bind=_connection)

    try:
        yield session
    finally:
        session.close()
        # Rollback to the savepoint so the next test starts clean
        if transaction.is_active:
            transaction.rollback()


# Alias for backwards compatibility
@pytest.fixture(name="db_session")
def db_session_fixture(db: Session):
    return db


# ─── App overrides (session-scoped, set once) ─────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_app_overrides(create_schema):
    """
    Override FastAPI dependencies for the entire test session.
    get_db → our test session
    get_current_user → a stable test user (created once)
    """
    from app.main import app
    from app.auth import get_current_user
    from app.db import get_db
    from app.models.user import User

    # Create one persistent test user for auth overrides
    _session = _TestSession(bind=_connection)
    _test_email = f"testuser-{uuid.uuid4().hex[:8]}@test.invalid"
    _user = User(email=_test_email, hashed_password="$2b$12$fakehashfakehash")
    _session.add(_user)
    _session.commit()
    _session.refresh(_user)

    def override_get_db():
        session = _TestSession(bind=_connection)
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user():
        """Return the stable session-level test user (no DB call needed)."""
        return _user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield

    app.dependency_overrides.clear()
    _session.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def unique_email() -> str:
    """Generate a collision-proof email for test fixtures."""
    return f"user-{uuid.uuid4().hex}@test.invalid"
