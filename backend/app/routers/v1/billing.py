from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth import get_current_user
from app.core.api_errors import server_error
from app.core.config import get_settings
from app.core.db import get_db
from app.models import User, Subscription
from app.services import stripe_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutRequest(BaseModel):
    plan: str # "pro" or "business"
    success_url: str
    cancel_url: str


@router.post("/checkout")
def create_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a Stripe payment session."""
    allowed_plans = ["pro", "business", "starter", "trader", "expert"]
    if payload.plan.lower() not in allowed_plans:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    
    try:
        checkout_url = stripe_service.create_checkout_session(
            db, current_user, payload.plan, payload.success_url, payload.cancel_url
        )
        return {"url": checkout_url}
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.get("/status")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription details."""
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub:
        return {"plan": "free", "status": "active"}
    
    return {
        "plan": sub.plan,
        "status": sub.status,
        "current_period_end": sub.current_period_end
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """Stripe webhook receiver (signature verified)."""
    settings = get_settings()
    if settings.is_production and not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    payload = await request.body()
    try:
        return stripe_service.handle_webhook_event(db, payload, stripe_signature)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook request",
        ) from None
    except Exception as e:
        raise server_error(logger, e) from e
