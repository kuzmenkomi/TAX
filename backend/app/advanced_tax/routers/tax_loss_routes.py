"""
Tax-Loss Harvesting API Routes
REST endpoints for tax-loss optimization features
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.advanced_tax.integration.database import get_db
from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
from app.advanced_tax.utils import ServiceException

router = APIRouter(
    prefix="/api/premium/tax-loss",
    tags=["tax-loss-harvesting"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)


@router.get(
    "/opportunities",
    summary="Get Tax-Loss Harvesting Opportunities",
    description="Scan user's portfolio and identify tax-loss harvesting opportunities",
    response_model=Dict[str, Any],
)
async def get_harvest_opportunities(
    country: str = Query("MX", description="Country code"),
    db: Session = Depends(get_db),
):
    """
    Scan user's portfolio for tax-loss harvesting opportunities.
    
    Returns opportunities ranked by potential tax savings.
    
    Query Parameters:
    - country: Tax country code (MX, BR, AR, etc.)
    
    Example response:
    ```
    {
        "status": "success",
        "opportunities": [
            {
                "asset": "BTC",
                "loss_amount": 2000,
                "tax_savings": 600,
                "priority_score": 95,
                ...
            }
        ]
    }
    ```
    """
    try:
        # TODO: Get user_id from JWT token
        user_id = 1  # Stub
        
        optimizer = TaxLossOptimizer(db, user_id, country)
        opportunities = optimizer.scan_portfolio()
        
        return {
            "status": "success",
            "opportunities": opportunities,
            "summary": optimizer.get_tax_impact_summary(),
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get(
    "/impact-summary",
    summary="Get Tax Impact Summary",
    description="Get total potential tax savings from all opportunities",
)
async def get_tax_impact(
    country: str = Query("MX"),
    db: Session = Depends(get_db),
):
    """
    Get summary of total tax savings available.
    
    Shows:
    - Total realizable losses
    - Potential tax savings
    - Number of opportunities
    - Top opportunities
    """
    try:
        user_id = 1  # Stub
        
        optimizer = TaxLossOptimizer(db, user_id, country)
        summary = optimizer.get_tax_impact_summary()
        
        return {
            "status": "success",
            "summary": summary,
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/execute/{opportunity_id}",
    summary="Execute Tax-Loss Harvest",
    description="Execute a tax-loss harvest: sell the losing position",
)
async def execute_harvest(
    opportunity_id: int,
    exchange_id: int = Query(..., description="Exchange ID for execution"),
    db: Session = Depends(get_db),
):
    """
    Execute tax-loss harvest for specified opportunity.
    
    Steps:
    1. Sells losing position at current price
    2. Locks in the tax loss
    3. Schedules rebuy reminder (after 30-day wash-sale period)
    
    Returns:
    - Action type (SELL)
    - Asset and quantity
    - Execution price
    - Estimated tax savings
    - Rebuy date (30 days later)
    """
    try:
        user_id = 1  # Stub
        
        optimizer = TaxLossOptimizer(db, user_id)
        result = optimizer.execute_harvest(opportunity_id)
        
        return {
            "status": "success",
            "action_executed": result,
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/execute-rebuy/{harvest_id}",
    summary="Execute Rebuy (After Wash-Sale Period)",
    description="Execute rebuy to lock in the tax loss benefit",
)
async def execute_rebuy(
    harvest_id: int,
    exchange_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Execute rebuy after wash-sale period expires.
    
    WARNING: Can only execute 30+ days after sale.
    Rebuy must be "substantially identical" asset.
    
    Returns execution details.
    """
    try:
        user_id = 1  # Stub
        
        optimizer = TaxLossOptimizer(db, user_id)
        # TODO: Implement
        
        return {
            "status": "success",
            "message": "Rebuy executed - tax loss now locked in",
        }
    
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    summary="Get Harvest History",
    description="Get all past harvests and their results",
)
async def get_harvest_history(
    year: int = Query(None, description="Filter by tax year"),
    db: Session = Depends(get_db),
):
    """
    Get complete history of tax-loss harvests.
    
    Shows:
    - All harvests executed
    - Results and outcomes
    - Tax savings realized
    - Status of each harvest
    """
    try:
        user_id = 1  # Stub
        
        optimizer = TaxLossOptimizer(db, user_id)
        # TODO: Fetch history from database
        
        return {
            "status": "success",
            "history": [],
            "total_realized_savings": 0,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status/{harvest_id}",
    summary="Get Harvest Status",
    description="Get current status of a harvest operation",
)
async def get_harvest_status(
    harvest_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed status of a harvest operation.
    
    Shows:
    - Current status
    - Execution date
    - Tax savings realized
    - Rebuy schedule (if applicable)
    """
    try:
        user_id = 1  # Stub
        
        # TODO: Query database for harvest
        
        return {
            "status": "success",
            "harvest": {},
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
