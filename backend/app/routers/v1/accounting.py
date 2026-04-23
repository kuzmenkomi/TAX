from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import User, LotMatch
from app.services.accounting_service import get_matches_for_transaction, get_matches_for_run

router = APIRouter(prefix="/accounting", tags=["Accounting"])

@router.get("/matches/transaction/{tx_id}")
def read_transaction_matches(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed lot matches for a specific transaction (Audit Trail).
    """
    matches = get_matches_for_transaction(db, current_user.id, tx_id)
    return {"matches": matches}

@router.get("/matches/run/{run_id}")
def read_run_matches(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all lot matches for a specific analysis run.
    """
    matches = get_matches_for_run(db, current_user.id, run_id)
    return {"matches": matches}
@router.post("/reports/pdf")
def download_pdf_report(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.report_service import ReportService
    from app.services.analysis_service import get_latest_analysis_result
    
    data = get_latest_analysis_result(db, current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="No analysis data found")
        
    return ReportService.generate_pdf_report(
        current_user, 
        req.get("jurisdiction", "BR"), 
        req.get("year", 2024), 
        data
    )

@router.post("/reports/turbotax")
def download_turbotax_csv(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.report_service import ReportService
    from app.services.analysis_service import get_latest_analysis_result
    
    data = get_latest_analysis_result(db, current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="No analysis data found")
        
    return ReportService.generate_turbotax_csv(data)
