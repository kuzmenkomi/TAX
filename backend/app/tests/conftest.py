import os
import sys
from pathlib import Path
import pytest
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force file-based DB for tests in a temporary location
_test_db_path = Path(__file__).resolve().parents[3] / "output" / "test_tax_app.db"
_test_db_path.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

# Ensure `import app...` works
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import Base
import app.models

_test_engine = create_engine(f"sqlite:///{_test_db_path}", connect_args={"check_same_thread": False})
_TestSession = sessionmaker(bind=_test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_test_engine)
    
    from app.main import app
    from app.auth import get_current_user
    from app.db import get_db
    
    def override_get_db():
        db = _TestSession()
        try:
            yield db
        finally:
            db.close()
            
    def override_get_current_user(db = Depends(override_get_db)):
        from app.models.user import User
        user = db.query(User).first()
        if not user:
            user = User(email="test@example.com", hashed_password="fake")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def db():
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def db_session(db):
    return db
