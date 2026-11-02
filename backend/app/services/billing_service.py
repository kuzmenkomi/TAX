from __future__ import annotations

from typing import Literal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, Subscription, WalletConnection, ExchangeConnection, Transaction

# Plan configurations
PLAN_LIMITS = {
    "free": {
        "max_wallets": 5,
        "max_exchanges": 5,
        "max_transactions": 25,
        "can_export_pdf": False,
        "can_use_ai": False,
    },
    "starter": {
        "max_wallets": 15,
        "max_exchanges": 15,
        "max_transactions": 150,
        "can_export_pdf": True,
        "can_use_ai": True,
    },
    "pro": {  # Synonym for starter
        "max_wallets": 15,
        "max_exchanges": 15,
        "max_transactions": 150,
        "can_export_pdf": True,
        "can_use_ai": True,
    },
    "trader": {
        "max_wallets": 999999,
        "max_exchanges": 999999,
        "max_transactions": 1000,
        "can_export_pdf": True,
        "can_use_ai": True,
    },
    "business": {  # Synonym for trader
        "max_wallets": 999999,
        "max_exchanges": 999999,
        "max_transactions": 1000,
        "can_export_pdf": True,
        "can_use_ai": True,
    },
    "expert": {
        "max_wallets": 999999,
        "max_exchanges": 999999,
        "max_transactions": 3000,
        "can_export_pdf": True,
        "can_use_ai": True,
    }
}


def get_user_plan(db: Session, user_id: int) -> str:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub or sub.status != "active":
        return "free"
    return sub.plan


def check_limit(
    db: Session, 
    user_id: int, 
    feature: Literal["wallets", "exchanges", "transactions", "pdf", "ai"]
):
    """Enforce plan limits. Raises HTTPException if limit exceeded."""
    plan = get_user_plan(db, user_id)
    limits = PLAN_LIMITS[plan]
    
    if feature == "pdf" and not limits["can_export_pdf"]:
        raise HTTPException(
            status_code=403, 
            detail="PDF Export is a Pro feature. Please upgrade your plan."
        )
    
    if feature == "ai" and not limits["can_use_ai"]:
        raise HTTPException(
            status_code=403, 
            detail="AI Insights are a Pro feature. Please upgrade your plan."
        )

    if feature == "wallets":
        count = db.query(WalletConnection).filter(WalletConnection.user_id == user_id).count()
        if count >= limits["max_wallets"]:
            raise HTTPException(
                status_code=403, 
                detail=f"Wallet limit reached ({limits['max_wallets']}) for {plan} plan."
            )

    if feature == "exchanges":
        count = db.query(ExchangeConnection).filter(ExchangeConnection.user_id == user_id).count()
        if count >= limits["max_exchanges"]:
            raise HTTPException(
                status_code=403, 
                detail=f"Exchange limit reached ({limits['max_exchanges']}) for {plan} plan."
            )

    if feature == "transactions":
        count = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        if count >= limits["max_transactions"]:
            raise HTTPException(
                status_code=403, 
                detail=f"Transaction limit reached ({limits['max_transactions']}) for {plan} plan."
            )
