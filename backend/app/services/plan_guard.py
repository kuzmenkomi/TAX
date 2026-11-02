from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.auth import get_current_user
from app.models import User
from app.services.billing_service import get_user_plan

def require_paid_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = get_user_plan(db, current_user.id)
    
    # Map plan names just in case
    # Current backend plans: "free", "pro", "business"
    # Current frontend plans: "free", "starter", "trader", "expert"
    if plan == "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "message": "This feature requires a paid subscription. Please upgrade.",
                "current_plan": "free"
            }
        )
    return plan
