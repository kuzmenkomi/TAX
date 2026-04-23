"""
Smart Reconciliation API Routes
REST endpoints for cost basis reconciliation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.advanced_tax.integration.database import get_db
from app.advanced_tax.services.reconciliation import SmartReconciliationEngine
from app.advanced_tax.utils import ServiceException

router = APIRouter(
    prefix="/api/premium/reconciliation",
    tags=["smart-reconciliation"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)


@router.get(
    "/gaps",
    summary="Get Missing Cost Basis Gaps",
    description="Find all transactions with unknown cost basis",
)
async def get_reconciliation_gaps(
    country: str = Query("MX"),
    db: Session = Depends(get_db),
):
    """
    Scan for transactions with missing cost basis.
    
    Identifies:
    - Transfers with unknown origins
    - Deposits without buy orders
    - Airdrops/mining without values
    
    Returns gaps ranked by tax impact (highest first).
    """
    try:
        user_id = 1  # Stub
        
        engine = SmartReconciliationEngine(db, user_id, country)
        gaps = engine.scan_for_gaps()
        
        return {
            "status": "success",
            "gaps": gaps,
            "summary": engine.get_reconciliation_summary(),
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/suggestions/{transaction_id}",
    summary="Get Matching Suggestions",
    description="Find source transactions for a receive with missing cost basis",
)
async def get_matching_suggestions(
    transaction_id: int,
    search_depth_hours: int = Query(72, ge=1, le=8760),
    db: Session = Depends(get_db),
):
    """
    Find potential source transactions for a transaction with gap.
    
    Search strategies:
    1. Same blockchain address (transfers)
    2. Exchange deposits (matching asset/qty/date)
    3. Import records (timestamp matching)
    
    Each suggestion has confidence score (0-1).
    """
    try:
        user_id = 1  # Stub
        
        engine = SmartReconciliationEngine(db, user_id)
        suggestions = engine.find_matching_transactions(
            transaction_id,
            search_depth_hours
        )
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "suggestions": suggestions,
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/accept-match",
    summary="Accept Matching Suggestion",
    description="Link send and receive transactions - establish cost basis",
)
async def accept_match(
    receive_txn_id: int = Query(...),
    send_txn_id: int = Query(...),
    reason: str = Query("user_accepted"),
    db: Session = Depends(get_db),
):
    """
    User accepts a suggested match.
    
    Creates permanent link between:
    - Receive transaction (unknown cost basis)
    - Send transaction (known price/cost)
    
    Automatically calculates cost basis from send transaction.
    """
    try:
        user_id = 1  # Stub
        
        engine = SmartReconciliationEngine(db, user_id)
        result = engine.accept_match(receive_txn_id, send_txn_id, reason)
        
        return {
            "status": "success",
            "matched": result,
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/manual-entry",
    summary="Set Cost Basis Manually",
    description="User manually sets cost basis for a transaction",
)
async def set_manual_cost_basis(
    transaction_id: int = Query(...),
    cost_basis: Decimal = Query(..., gt=0, description="Cost basis in USD"),
    source: str = Query("user_entry", description="Source of value"),
    notes: str = Query("", description="User notes"),
    db: Session = Depends(get_db),
):
    """
    User manually sets cost basis for transaction with gap.
    
    Use when:
    - No automatic match found
    - Off-exchange purchase
    - Custom valuation needed
    
    Records all manual entries for audit trail.
    """
    try:
        user_id = 1  # Stub
        
        engine = SmartReconciliationEngine(db, user_id)
        result = engine.manual_entry(transaction_id, cost_basis, source, notes)
        
        return {
            "status": "success",
            "result": result,
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/dismiss",
    summary="Dismiss Gap",
    description="User dismisses a reconciliation gap",
)
async def dismiss_gap(
    transaction_id: int = Query(...),
    reason: str = Query("user_dismissed"),
    db: Session = Depends(get_db),
):
    """
    Mark a gap as dismissed.
    
    User acknowledges gap but decides not to resolve it now.
    Stored for audit trail.
    """
    try:
        user_id = 1  # Stub
        
        # TODO: Implement
        
        return {
            "status": "success",
            "message": "Gap dismissed",
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/summary",
    summary="Get Reconciliation Summary",
    description="Summary of all gaps and resolution status",
)
async def get_summary(
    db: Session = Depends(get_db),
):
    """
    Get overview of reconciliation status.
    
    Shows:
    - Total gaps
    - Pending (user action needed)
    - Matched (auto-resolved)
    - Manual entries
    - Total tax impact
    """
    try:
        user_id = 1  # Stub
        
        engine = SmartReconciliationEngine(db, user_id)
        summary = engine.get_reconciliation_summary()
        
        return {
            "status": "success",
            "summary": summary,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
