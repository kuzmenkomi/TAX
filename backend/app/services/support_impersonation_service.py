"""Support impersonation rules + audit log writes — separate from HTTP layer."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.models import User
from app.models.support_impersonation import SupportImpersonationLog

logger = logging.getLogger(__name__)

STAFF_ROLES = frozenset({"support", "admin"})
SUPPORT_ACCESS_DURATION = timedelta(days=30)


def support_access_public_fields(user: User) -> tuple[str | None, bool]:
    """ISO expiry + whether customer support window is active."""
    until = getattr(user, "allow_support_until", None)
    if until is None:
        return None, False
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    active = until > now
    return until.isoformat(), active


def assert_staff(user: User) -> None:
    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support or admin role required.",
        )


def _subject_eligible(subject: User) -> bool:
    return subject.role == "user" and subject.is_active


def lookup_subject_user(db: Session, *, user_id: int | None, email: str | None) -> User:
    if user_id is not None:
        u = db.query(User).filter(User.id == user_id).first()
    elif email:
        u = db.query(User).filter(User.email == email.strip().lower()).first()
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_id or email required")
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return u


def start_impersonation(
    db: Session,
    *,
    actor: User,
    subject: User,
    reason: str,
    request: Request | None = None,
) -> SupportImpersonationLog:
    assert_staff(actor)
    if actor.id == subject.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot impersonate yourself")
    if not _subject_eligible(subject):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active customer accounts (role=user) can be viewed.",
        )
    reason_clean = (reason or "").strip()
    if len(reason_clean) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reason must be at least 8 characters (ticket id, case note, etc.).",
        )

    ip = None
    if request is not None and request.client:
        ip = request.client.host[:64] if request.client.host else None

    log = SupportImpersonationLog(
        actor_user_id=actor.id,
        subject_user_id=subject.id,
        reason=reason_clean,
        started_at=datetime.now(timezone.utc),
        actor_ip=ip,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    logger.warning(
        "SUPPORT_IMPERSONATION_START actor_id=%s subject_id=%s log_id=%s ip=%s",
        actor.id,
        subject.id,
        log.id,
        ip,
    )
    return log


def active_log_for_token(db: Session, log_id: int) -> SupportImpersonationLog | None:
    return (
        db.query(SupportImpersonationLog)
        .filter(
            SupportImpersonationLog.id == log_id,
            SupportImpersonationLog.ended_at.is_(None),
        )
        .first()
    )


def end_impersonation(db: Session, log: SupportImpersonationLog) -> None:
    log.ended_at = datetime.now(timezone.utc)
    db.commit()
    logger.warning("SUPPORT_IMPERSONATION_END log_id=%s", log.id)
