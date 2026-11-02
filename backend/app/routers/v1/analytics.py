import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.api_errors import server_error
from app.core.db import get_db
from app.models import User
from app.services.threshold_service import ThresholdService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/thresholds/{jurisdiction}")
async def get_tax_thresholds(
    jurisdiction: str = "BR",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get monthly tax-free threshold status for a specific jurisdiction.
    Currently supported: BR (Brazil)
    """
    try:
        status = ThresholdService.get_monthly_status(db, current_user.id, jurisdiction)
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e
