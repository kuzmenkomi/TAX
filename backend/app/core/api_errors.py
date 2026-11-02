"""Stable API error responses — never leak exception strings to clients."""

from __future__ import annotations

import logging
import uuid
from typing import Never

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _ref() -> str:
    return uuid.uuid4().hex[:12]


def server_error(
    log: logging.Logger,
    exc: BaseException,
    *,
    public_message: str = "An unexpected error occurred. Please try again later.",
) -> HTTPException:
    """Log full exception; return opaque HTTP 500."""
    rid = _ref()
    log.exception("server_error ref=%s", rid, exc_info=exc)
    return HTTPException(
        status_code=500,
        detail=f"{public_message} (ref {rid})",
    )


def bad_request_from_exc(
    log: logging.Logger,
    exc: BaseException,
    *,
    public_message: str = "Invalid request.",
) -> HTTPException:
    """Use for unexpected parsing/handling errors on 400-class paths."""
    rid = _ref()
    log.warning("bad_request ref=%s: %s", rid, exc, exc_info=True)
    return HTTPException(status_code=400, detail=f"{public_message} (ref {rid})")


def re_raise_http(exc: BaseException) -> Never:
    raise exc


__all__ = ["server_error", "bad_request_from_exc", "re_raise_http"]
