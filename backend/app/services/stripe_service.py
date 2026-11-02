from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import User, Subscription

logger = logging.getLogger(__name__)


def init_stripe():
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    db: Session, 
    user: User, 
    plan_name: str, 
    success_url: str, 
    cancel_url: str
) -> str:
    """Create a Stripe Checkout Session for a subscription."""
    init_stripe()
    settings = get_settings()
    
    stripe_plan = plan_name.lower()
    if stripe_plan in ["starter", "pro"]:
        price_id = settings.stripe_price_pro
    elif stripe_plan in ["trader", "expert", "business"]:
        price_id = settings.stripe_price_business
    else:
        price_id = None
        
    if not price_id:
        raise ValueError(f"No Stripe price configured for plan {plan_name!r}")
    
    # Get or create subscription info to find/set stripe_customer_id
    sub_info = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub_info:
        sub_info = Subscription(user_id=user.id)
        db.add(sub_info)
        db.commit()
    
    # If user doesn't have a customer ID yet, create one in Stripe
    if not sub_info.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": user.id}
        )
        sub_info.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=sub_info.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user.id, "plan": plan_name}
    )
    
    return session.url


def handle_webhook_event(db: Session, payload: bytes, sig_header: str | None):
    """Process incoming Stripe webhook events (signature verified)."""
    settings = get_settings()
    if not sig_header:
        raise ValueError("Missing Stripe-Signature header")
    if not (settings.STRIPE_WEBHOOK_SECRET or "").strip():
        raise ValueError("Stripe webhook secret not configured")
    init_stripe()

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        raise ValueError("Invalid webhook signature") from e
    except ValueError as e:
        logger.warning("Stripe webhook payload error: %s", e)
        raise

    # Handle the event
    if event.type == "checkout.session.completed":
        session = event.data.object
        user_id = session.metadata.get("user_id")
        plan = session.metadata.get("plan")
        stripe_sub_id = session.subscription
        
        _update_subscription(db, user_id, plan, "active", stripe_sub_id)
        logger.info(f"Subscription activated for user {user_id}")

    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        user_id = subscription.metadata.get("user_id")
        status = subscription.status
        
        # Map stripe status to our simple status if needed
        _update_subscription(db, user_id, status=status)

    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        user_id = subscription.metadata.get("user_id")
        _update_subscription(db, user_id, plan="free", status="canceled")
        logger.info(f"Subscription canceled for user {user_id}")

    return {"status": "success"}


def _update_subscription(
    db: Session, 
    user_id: int, 
    plan: Optional[str] = None, 
    status: Optional[str] = None,
    stripe_sub_id: Optional[str] = None
):
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub:
        if plan: sub.plan = plan
        if status: sub.status = status
        if stripe_sub_id: sub.stripe_subscription_id = stripe_sub_id
        db.commit()
