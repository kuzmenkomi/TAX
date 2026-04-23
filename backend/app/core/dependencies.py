from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user as _get_current_user
from app.core.db import get_db
from app.models import User


def get_current_user(
    db: Session = Depends(get_db),
    user: User = Depends(_get_current_user),
) -> User:
    """Shared dependency wrapper for authenticated users."""
    return user
