from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health_check(request: Request) -> dict[str, str]:
    return {"status": "ok", "version": request.app.version}
