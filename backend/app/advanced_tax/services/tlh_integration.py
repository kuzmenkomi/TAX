"""
TLH INTEGRATION GUIDE
How to integrate Event-Driven TLH into FastAPI backend
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import logging

from ..services.tlh_engine import TLHEngine, RecommendationStatus, ExecutionPlan
from ..services.tlh_scorer import TLHScorer
from ..services.tlh_executor import TLHExecutor
from ..services.tlh_event_listener import TLHEventListener, TLHEventReactor
from ..models import User, Portfolio

logger = logging.getLogger(__name__)

# ============================================================================
# INITIALIZE COMPONENTS (do this in main.py or startup event)
# ============================================================================

def initialize_tlh_system(app):
    """Initialize TLH system on app startup"""
    
    logger.info("🚀 Initializing TLH System...")
    
    # Create components
    scorer = TLHScorer()
    executor = TLHExecutor()
    listener = TLHEventListener()
    
    # Create reactor
    reactor = TLHEventReactor(None)  # Pass actual optimizer_service in real code
    reactor.set_default_reactions()
    listener.subscribe(reactor.on_event)
    
    # Create engine
    engine = TLHEngine(
        scorer=scorer,
        executor=executor,
        event_listener=listener,
        event_reactor=reactor,
        db_service=None  # Inject your DB service
    )
    
    # Store in app state
    app.state.tlh_engine = engine
    app.state.price_listener = listener
    
    logger.info("✅ TLH System ready")
    return engine, listener


# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter(prefix="/api/v1/tlh", tags=["tax-loss-harvesting"])


@router.post("/scan")
async def scan_portfolio(user: User, background_tasks: BackgroundTasks):
    """
    Scan user's portfolio for tax-loss harvesting opportunities
    
    Returns:
        List of TLHRecommendation objects sorted by priority_score desc
    """
    engine = get_engine()
    
    try:
        # Get user's portfolio
        portfolio = await get_user_portfolio(user)
        
        # Scan for opportunities
        recommendations = engine.scan_portfolio(portfolio)
        
        logger.info(f"✅ Scan complete: {len(recommendations)} opportunities found")
        
        return {
            'success': True,
            'count': len(recommendations),
            'recommendations': [r.to_dict() for r in recommendations]
        }
    
    except Exception as e:
        logger.error(f"❌ Scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_recommendations(
    user: User,
    status: Optional[str] = None,
    asset: Optional[str] = None
):
    """
    Get user's current TLH recommendations
    
    Query params:
        status: "new", "reviewed", "approved", "executed", "failed"
        asset: filter by specific asset
    """
    engine = get_engine()
    
    try:
        # Filter by status if provided
        rec_status = RecommendationStatus[status.upper()] if status else None
        recommendations = engine.get_recommendations(status=rec_status)
        
        # Filter by asset if provided
        if asset:
            recommendations = [r for r in recommendations if r['asset'] == asset]
        
        return {
            'success': True,
            'count': len(recommendations),
            'recommendations': recommendations
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/{position_id}")
async def get_recommendation(user: User, position_id: str):
    """Get specific recommendation details"""
    engine = get_engine()
    
    rec = engine.get_recommendation(position_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {
        'success': True,
        'recommendation': rec
    }


@router.post("/recommendations/{position_id}/approve")
async def approve_recommendation(user: User, position_id: str):
    """User approves a recommendation"""
    engine = get_engine()
    
    try:
        engine.approve_recommendation(position_id)
        return {'success': True, 'message': 'Recommendation approved'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommendations/{position_id}/cancel")
async def cancel_recommendation(user: User, position_id: str):
    """User cancels a recommendation"""
    engine = get_engine()
    
    try:
        engine.cancel_recommendation(position_id)
        return {'success': True, 'message': 'Recommendation cancelled'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan/create")
async def create_execution_plan(
    user: User,
    recommendation_ids: List[str],
    strategy: str = "immediate"
):
    """
    Create execution plan for selected recommendations
    
    Request body:
        {
            "recommendation_ids": ["pos_btc_001", "pos_eth_001"],
            "strategy": "immediate"  # or "limit_price", "scheduled"
        }
    """
    engine = get_engine()
    
    try:
        plan = engine.create_execution_plan(recommendation_ids, strategy)
        
        return {
            'success': True,
            'plan': {
                'num_recommendations': len(plan.recommendations),
                'estimated_tax_savings': float(plan.estimated_tax_savings),
                'estimated_fees': float(plan.estimated_fees),
                'estimated_capital_needed': float(plan.estimated_capital_needed),
                'recommendations': [r.to_dict() for r in plan.recommendations]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan/execute")
async def execute_plan(
    user: User,
    background_tasks: BackgroundTasks,
    dry_run: bool = True,
    strategy: str = "immediate"
):
    """
    Execute execution plan
    
    Request body:
        {
            "dry_run": true,           # Simulate first
            "strategy": "immediate"     # or "limit_price", "scheduled"
        }
    """
    engine = get_engine()
    
    try:
        # Get latest plan
        if not engine.execution_plans:
            raise HTTPException(status_code=400, detail="No execution plan created")
        
        plan = list(engine.execution_plans.values())[-1]
        
        # Execute plan (async)
        background_tasks.add_task(
            run_execution,
            engine=engine,
            plan=plan,
            dry_run=dry_run,
            strategy=strategy
        )
        
        return {
            'success': True,
            'message': f'Execution started (dry_run={dry_run})',
            'status': 'executing'
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_execution_history(user: User, limit: int = 100):
    """Get execution history"""
    engine = get_engine()
    
    history = engine.get_execution_history(limit)
    
    return {
        'success': True,
        'count': len(history),
        'history': history
    }


# ============================================================================
# EVENT LISTENER API
# ============================================================================

@router.post("/events/price-update")
async def on_price_update(asset: str, price: float, timestamp: datetime = None):
    """
    Price update from external service
    Triggers TLH recalculation if price drops sufficiently
    """
    listener = get_event_listener()
    
    try:
        event = listener.on_price_update(asset, Decimal(str(price)))
        
        if event:
            logger.info(f"📊 Price event for {asset}: {event.event_type.value}")
            return {
                'success': True,
                'event_triggered': True,
                'event': event.to_dict()
            }
        else:
            return {
                'success': True,
                'event_triggered': False,
                'message': f'Price update recorded (no threshold crossed)'
            }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events/register-asset")
async def register_asset_for_monitoring(
    asset: str,
    drop_threshold_pct: float = 5.0,
    purchase_price: float = None
):
    """Register asset for price monitoring"""
    listener = get_event_listener()
    
    try:
        listener.register_asset(
            asset=asset,
            drop_threshold_pct=drop_threshold_pct,
            purchase_price=Decimal(str(purchase_price)) if purchase_price else None
        )
        
        return {
            'success': True,
            'message': f'{asset} registered for monitoring'
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/history")
async def get_event_history(asset: Optional[str] = None):
    """Get price event history"""
    listener = get_event_listener()
    
    history = listener.get_event_history(asset=asset)
    
    return {
        'success': True,
        'count': len(history),
        'events': history
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_engine() -> TLHEngine:
    """Get TLH engine from app state"""
    from fastapi import Request
    # In real code: use Request context to get app
    # For now: return global reference
    return TLHEngine()  # Would be: Request.app.state.tlh_engine


def get_event_listener() -> TLHEventListener:
    """Get price event listener from app state"""
    from fastapi import Request
    return TLHEventListener()  # Would be: Request.app.state.price_listener


async def get_user_portfolio(user: User) -> List[dict]:
    """Get user's portfolio positions"""
    # In real code: query database
    # Return list of position dicts with {
    #     'id': position_id,
    #     'asset': symbol,
    #     'quantity': qty,
    #     'average_cost': cost_basis,
    #     'current_price': current_price,
    #     'purchase_date': datetime,
    #     'exchanges': [list]
    # }
    return []


async def run_execution(
    engine: TLHEngine,
    plan: ExecutionPlan,
    dry_run: bool = True,
    strategy: str = "immediate"
):
    """Execute plan in background"""
    try:
        logger.info(f"🚀 Starting execution (dry_run={dry_run})...")
        
        # This would be awaited in real async code
        results = engine.execute_plan(plan, dry_run=dry_run, strategy=strategy)
        
        logger.info(f"✅ Execution complete")
        
        # In real code: update database, send notification
        
    except Exception as e:
        logger.error(f"❌ Execution failed: {str(e)}")


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

"""
TODO:
□ 1. Add to main.py startup:
    initialize_tlh_system(app)

□ 2. Create database models:
    - TLHRecommendation (ORM model)
    - TLHExecutionHistory (log all executions)
    - PriceEvent (log all price events)

□ 3. Connect to price feeds:
    - CoinCap API for real-time prices
    - Call on_price_update() on each update

□ 4. Connect portfolio data:
    - Fetch from User's exchanges
    - Calculate cost basis (FIFO/LIFO/AVCO)
    - Get current prices

□ 5. Add authentication:
    - Verify user owns positions
    - Encrypt exchange keys
    - Scope API to user

□ 6. Create frontend:
    - Scan button
    - Recommendations list
    - Approve/cancel UI
    - Execution preview
    - History view

□ 7. Add tests:
    - MockTLHEngine for testing
    - Test all endpoints
    - Test event triggering

□ 8. Add monitoring:
    - Log all decisions
    - Track execution success rate
    - Dashboard of TLH metrics

□ 9. Add configuration:
    - Min score to recommend
    - Min score to auto-execute
    - Min loss amount
    - Max concurrent executions

□ 10. Add API documentation:
    - OpenAPI/Swagger docs
    - Example request/response
    - Rate limiting
"""


# ============================================================================
# EXAMPLE: COMPLETE FLOW IN PYTHON
# ============================================================================

async def example_complete_flow():
    """Example: Complete TLH flow"""
    
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    # Initialize
    print("\n" + "="*60)
    print("TLH COMPLETE FLOW EXAMPLE")
    print("="*60 + "\n")
    
    scorer = TLHScorer()
    executor = TLHExecutor()
    listener = TLHEventListener()
    engine = TLHEngine(scorer=scorer, executor=executor, event_listener=listener)
    
    # Step 1: Register assets for price monitoring
    print("1️⃣ REGISTER ASSETS")
    listener.register_asset("BTC", drop_threshold_pct=5.0)
    listener.register_asset("ETH", drop_threshold_pct=5.0)
    print("   ✅ BTC and ETH registered\n")
    
    # Step 2: Simulate portfolio
    print("2️⃣ PORTFOLIO POSITIONS")
    portfolio = [
        {
            'id': 'pos_btc_001',
            'asset': 'BTC',
            'quantity': Decimal('1.5'),
            'average_cost': Decimal('35000'),
            'current_price': Decimal('30000'),
            'purchase_date': datetime.now() - timedelta(days=180),
            'exchanges': ['binance']
        },
        {
            'id': 'pos_eth_001',
            'asset': 'ETH',
            'quantity': Decimal('10'),
            'average_cost': Decimal('2500'),
            'current_price': Decimal('2000'),
            'purchase_date': datetime.now() - timedelta(days=90),
            'exchanges': ['kraken']
        }
    ]
    for pos in portfolio:
        loss = (Decimal(pos['average_cost']) - Decimal(pos['current_price'])) * Decimal(pos['quantity'])
        print(f"   {pos['asset']}: Loss of ${loss:.2f}")
    print()
    
    # Step 3: Scan portfolio
    print("3️⃣ SCAN PORTFOLIO")
    recommendations = engine.scan_portfolio(portfolio)
    for rec in recommendations:
        print(f"   {rec.asset}: Score {rec.priority_score:.1f} - {rec.explanation[:40]}")
    print()
    
    # Step 4: Create execution plan
    print("4️⃣ CREATE EXECUTION PLAN")
    if recommendations:
        plan = engine.create_execution_plan([r.position_id for r in recommendations])
        print(f"   Plan: {len(plan.recommendations)} recs")
        print(f"   Estimated tax savings: ${plan.estimated_tax_savings:.2f}")
        print(f"   Estimated fees: ${plan.estimated_fees:.2f}\n")
        
        # Step 5: Dry run execution
        print("5️⃣ DRY RUN EXECUTION")
        results = engine.execute_plan(plan, dry_run=True)
        print(f"   Successful: {len(results['successful'])}")
        print(f"   Failed: {len(results['failed'])}\n")
        
        # Step 6: Simulate price event
        print("6️⃣ PRICE EVENT (BTC drops 5%)")
        event = listener.on_price_update("BTC", Decimal("28500"))
        if event:
            print(f"   ✨ Event triggered: {event.event_type.value}")
            print(f"   Price change: {event.price_change_pct:.1f}%\n")
        
        # Step 7: Get recommendations again
        print("7️⃣ CURRENT RECOMMENDATIONS")
        recs = engine.get_recommendations()
        print(f"   Total: {len(recs)}")
        for rec in recs:
            print(f"   - {rec['asset']}: {rec['status']} (score {rec['priority_score']:.1f})")
    
    print("\n" + "="*60)
    print("✅ COMPLETE FLOW DEMO")
    print("="*60 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_complete_flow())
