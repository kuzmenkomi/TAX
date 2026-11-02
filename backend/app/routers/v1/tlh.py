"""
TLH (Tax-Loss Harvesting) API Router
20+ endpoints for TLH operations: scan, recommend, execute, track
"""

from datetime import datetime, timedelta
import uuid
import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.api_errors import server_error
from app.core.db import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models import (
    TLHOpportunity,
    TLHExecutionHistory,
    RecommendationStatus,
    ExecutionStrategy,
    PriceEvent,
)
from app.schemas.tlh_schemas import (
    TLHOpportunityResponse,
    TLHOpportunityCreate,
    TLHOpportunityUpdate,
    TLHOpportunityExecute,
    TLHExecutionHistoryResponse,
    TLHExecutionResult,
    TLHScanResult,
    TLHMetrics,
    BulkExecuteRequest,
    BulkExecuteResponse,
)

# Import services from advanced_tax module
try:
    from app.advanced_tax.services.tlh_engine import TLHEngine
    from app.advanced_tax.services.tlh_scorer import TLHScorer
    from app.advanced_tax.services.tlh_executor import TLHExecutor
    from app.advanced_tax.services.tlh_event_listener import TLHEventListener
except ImportError:
    # Fallback if not available
    TLHEngine = None
    TLHScorer = None
    TLHExecutor = None
    TLHEventListener = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tlh", tags=["TLH"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_tlh_scanner(db: Session = Depends(get_db)):
    """Get TLH scanner instance"""
    if TLHEngine is None:
        raise HTTPException(status_code=500, detail="TLH Engine not available")
    return TLHEngine(db_service=db)


# ============================================================================
# SCAN & DISCOVER ENDPOINTS
# ============================================================================

@router.post("/scan", response_model=TLHScanResult)
def scan_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scan portfolio for TLH opportunities
    """
    try:
        from app.services.tlh_bridge_service import TLHBridgeService
        
        # Run the real bridge scan
        scan_results = TLHBridgeService.run_scan(db, current_user.id)
        
        # Fetch the newly created opportunities
        opportunities = db.query(TLHOpportunity).filter(
            TLHOpportunity.user_id == str(current_user.id),
            TLHOpportunity.status == RecommendationStatus.NEW.value
        ).all()
        
        return TLHScanResult(
            opportunities_found=scan_results["opportunities_found"],
            total_harvestable_losses=scan_results["total_harvestable_losses"],
            total_tax_benefit=scan_results["total_tax_benefit"],
            opportunities=opportunities
        )
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        raise server_error(logger, e)


@router.get("/opportunities", response_model=list[TLHOpportunityResponse])
def list_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    asset: Optional[str] = Query(None),
    min_loss: Optional[Decimal] = Query(None),
):
    """
    List all TLH opportunities with filtering
    """
    try:
        user_id = str(current_user.id)
        query = db.query(TLHOpportunity).filter(TLHOpportunity.user_id == user_id)
        
        if status:
            query = query.filter(TLHOpportunity.status == status)
        if asset:
            query = query.filter(TLHOpportunity.asset == asset)
        if min_loss:
            query = query.filter(TLHOpportunity.loss_amount >= min_loss)
        
        opportunities = query.all()
        return opportunities
    except Exception as e:
        logger.error(f"List opportunities failed: {str(e)}")
        raise server_error(logger, e)


@router.get("/opportunities/{opportunity_id}", response_model=TLHOpportunityResponse)
def get_opportunity(
    opportunity_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific opportunity details"""
    try:
        user_id = str(current_user.id)
        opportunity = db.query(TLHOpportunity).filter(
            TLHOpportunity.id == opportunity_id,
            TLHOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return opportunity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get opportunity failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# CREATE & MANAGE OPPORTUNITIES
# ============================================================================

@router.post("/opportunities", response_model=TLHOpportunityResponse)
def create_opportunity(
    request: TLHOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new TLH opportunity manually
    """
    try:
        user_id = str(current_user.id)
        opportunity = TLHOpportunity(
            id=str(uuid.uuid4()),
            user_id=user_id,
            position_id=request.position_id,
            asset=request.asset,
            loss_amount=request.loss_amount,
            tax_rate=request.tax_rate,
            priority_score=request.priority_score,
            explanation=request.explanation,
            status=RecommendationStatus.NEW.value,
        )
        
        db.add(opportunity)
        db.commit()
        db.refresh(opportunity)
        
        logger.info(f"Created opportunity {opportunity.id}")
        return opportunity
    except Exception as e:
        db.rollback()
        logger.error(f"Create opportunity failed: {str(e)}")
        raise server_error(logger, e)


@router.put("/opportunities/{opportunity_id}", response_model=TLHOpportunityResponse)
def update_opportunity(
    opportunity_id: str = Path(...),
    request: TLHOpportunityUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update opportunity (status, notes, strategy)"""
    try:
        user_id = str(current_user.id)
        opportunity = db.query(TLHOpportunity).filter(
            TLHOpportunity.id == opportunity_id,
            TLHOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if request.status:
            opportunity.status = request.status
        if request.execution_strategy:
            opportunity.execution_strategy = request.execution_strategy
        if request.notes:
            opportunity.notes = request.notes
        
        opportunity.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(opportunity)
        
        return opportunity
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update opportunity failed: {str(e)}")
        raise server_error(logger, e)


@router.delete("/opportunities/{opportunity_id}")
def delete_opportunity(
    opportunity_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete/cancel opportunity"""
    try:
        user_id = str(current_user.id)
        opportunity = db.query(TLHOpportunity).filter(
            TLHOpportunity.id == opportunity_id,
            TLHOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        opportunity.status = RecommendationStatus.CANCELLED.value
        db.commit()
        
        return {"status": "cancelled", "opportunity_id": opportunity_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete opportunity failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# EXECUTION ENDPOINTS
# ============================================================================

@router.post("/opportunities/{opportunity_id}/execute", response_model=TLHExecutionResult)
def execute_opportunity(
    opportunity_id: str = Path(...),
    request: TLHOpportunityExecute = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute single opportunity
    """
    try:
        user_id = str(current_user.id)
        # Get opportunity
        opportunity = db.query(TLHOpportunity).filter(
            TLHOpportunity.id == opportunity_id,
            TLHOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Validate strategy
        if request.strategy not in [s.value for s in ExecutionStrategy]:
            raise HTTPException(status_code=400, detail="Invalid execution strategy")
        
        # Update status
        if request.dry_run:
            opportunity.status = RecommendationStatus.DRY_RUN_PENDING.value
        else:
            opportunity.status = RecommendationStatus.EXECUTING.value
        
        opportunity.execution_strategy = request.strategy
        opportunity.execution_attempts += 1
        
        # Create execution history
        execution = TLHExecutionHistory(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity.id,
            strategy=request.strategy,
            status="pending" if request.dry_run else "executing",
            dry_run=request.dry_run,
        )
        
        db.add(opportunity)
        db.add(execution)
        db.commit()
        db.refresh(opportunity)
        
        logger.info(f"Executed opportunity {opportunity_id} with strategy {request.strategy}")
        
        return TLHExecutionResult(
            success=True,
            opportunity_id=opportunity.id,
            status=opportunity.status,
            message=f"Execution initiated with {request.strategy} strategy",
            dry_run=request.dry_run,
            quantity_executed=opportunity.quantity_executed,
            fees_paid=opportunity.fees_paid,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Execute opportunity failed: {str(e)}")
        raise server_error(logger, e)


@router.post("/bulk-execute", response_model=BulkExecuteResponse)
def bulk_execute(
    request: BulkExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute multiple opportunities at once
    """
    try:
        user_id = str(current_user.id)
        results = []
        successful = 0
        failed = 0
        pending = 0
        total_loss = Decimal(0)
        
        # Get all opportunities
        opportunities = db.query(TLHOpportunity).filter(
            TLHOpportunity.user_id == user_id,
            TLHOpportunity.id.in_(request.opportunity_ids)
        ).all()
        
        if not opportunities:
            raise HTTPException(status_code=404, detail="No opportunities found")
        
        # Execute each
        for opp in opportunities:
            try:
                opp.execution_strategy = request.strategy
                opp.execution_attempts += 1
                
                if request.dry_run:
                    opp.status = RecommendationStatus.DRY_RUN_PENDING.value
                else:
                    opp.status = RecommendationStatus.EXECUTING.value
                
                execution = TLHExecutionHistory(
                    id=str(uuid.uuid4()),
                    opportunity_id=opp.id,
                    strategy=request.strategy,
                    status="pending",
                    dry_run=request.dry_run,
                )
                
                db.add(opp)
                db.add(execution)
                
                total_loss += opp.loss_amount
                
                if request.dry_run:
                    pending += 1
                    status = "pending"
                else:
                    successful += 1
                    status = "executing"
                
                results.append(TLHExecutionResult(
                    success=True,
                    opportunity_id=opp.id,
                    status=status,
                    message=f"Queued for {request.strategy} execution",
                    dry_run=request.dry_run,
                ))
            except Exception as e:
                failed += 1
                results.append(TLHExecutionResult(
                    success=False,
                    opportunity_id=opp.id,
                    status="failed",
                    message=str(e),
                    dry_run=request.dry_run,
                ))
        
        db.commit()
        
        total_tax_benefit = total_loss * Decimal('0.24')
        
        return BulkExecuteResponse(
            total_opportunities=len(request.opportunity_ids),
            successful=successful,
            failed=failed,
            pending=pending,
            total_harvestable_loss=total_loss,
            total_tax_benefit=total_tax_benefit,
            results=results,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk execute failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# EXECUTION HISTORY
# ============================================================================

@router.get("/opportunities/{opportunity_id}/history", response_model=list[TLHExecutionHistoryResponse])
def get_execution_history(
    opportunity_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution history for opportunity"""
    try:
        user_id = str(current_user.id)
        # Verify ownership
        opportunity = db.query(TLHOpportunity).filter(
            TLHOpportunity.id == opportunity_id,
            TLHOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Get history
        history = db.query(TLHExecutionHistory).filter(
            TLHExecutionHistory.opportunity_id == opportunity_id
        ).order_by(TLHExecutionHistory.executed_at.desc()).all()
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# PRICE EVENTS & MONITORING
# ============================================================================

@router.get("/events", response_model=list)
def get_price_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset: Optional[str] = Query(None),
    hours: int = Query(24),
):
    """Get recent price events"""
    try:
        user_id = str(current_user.id)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(PriceEvent).filter(
            PriceEvent.user_id == user_id,
            PriceEvent.timestamp >= cutoff_time
        )
        
        if asset:
            query = query.filter(PriceEvent.asset == asset)
        
        events = query.order_by(PriceEvent.timestamp.desc()).all()
        return events
    except Exception as e:
        logger.error(f"Get events failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/metrics", response_model=TLHMetrics)
def get_tlh_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get TLH system metrics and statistics"""
    try:
        user_id = str(current_user.id)
        # Get all opportunities
        opportunities = db.query(TLHOpportunity).filter(TLHOpportunity.user_id == user_id).all()
        
        # Calculate metrics
        total_loss = sum(Decimal(o.loss_amount) for o in opportunities)
        total_tax_benefit = total_loss * Decimal('0.24')
        avg_score = sum(o.priority_score for o in opportunities) / len(opportunities) if opportunities else 0
        wash_sale_risks = sum(1 for o in opportunities if o.wash_sale_risk)
        executed = sum(1 for o in opportunities if o.status == RecommendationStatus.EXECUTED.value)
        pending = sum(1 for o in opportunities if o.status in [
            RecommendationStatus.PENDING.value,
            RecommendationStatus.EXECUTING.value
        ])
        failed = sum(1 for o in opportunities if o.status == RecommendationStatus.FAILED.value)
        success_rate = executed / (executed + failed) if (executed + failed) > 0 else 0
        opps_with_fees = [o for o in opportunities if o.fees_paid]
        avg_fees = (
            sum(o.fees_paid for o in opps_with_fees) / len(opps_with_fees)
            if opps_with_fees else Decimal(0)
        )
        
        return TLHMetrics(
            total_harvestable_losses=total_loss,
            total_tax_benefit=total_tax_benefit,
            average_priority_score=avg_score,
            wash_sale_risks=wash_sale_risks,
            executed_opportunities=executed,
            pending_executions=pending,
            success_rate=success_rate,
            average_fees=avg_fees or Decimal(0),
        )
    except Exception as e:
        logger.error(f"Get metrics failed: {str(e)}")
        raise server_error(logger, e)


# ============================================================================
# STATUS & HEALTH
# ============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tlh",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
    }
