# TLH Engine - Quick Reference Guide

## Installation

```bash
# Copy files to backend
cp tlh_scorer.py backend/app/services/
cp tlh_executor.py backend/app/services/
cp tlh_event_listener.py backend/app/services/
cp tlh_engine.py backend/app/services/
```

## Quick Start

### 1. Initialize System (in main.py)
```python
from fastapi import FastAPI
from app.services.tlh_engine import initialize_tlh_system

app = FastAPI()

@app.on_event("startup")
async def startup():
    engine, listener = initialize_tlh_system(app)

# Include TLH routes
from app.services.tlh_integration import router
app.include_router(router)
```

### 2. Scan for Opportunities
```python
# API call
POST /api/v1/tlh/scan

# Returns:
{
  "success": true,
  "count": 2,
  "recommendations": [
    {
      "asset": "BTC",
      "loss_amount": 5000,
      "priority_score": 89.3,
      "priority_breakdown": {
        "tax_savings_component": 35.2,
        "liquidity_component": 30.1,
        ...
      },
      "explanation": "🔥 Excellent opportunity - execute immediately"
    }
  ]
}
```

### 3. Create Execution Plan
```python
# API call
POST /api/v1/tlh/plan/create
{
  "recommendation_ids": ["pos_btc_001", "pos_eth_001"],
  "strategy": "immediate"
}

# Returns:
{
  "num_recommendations": 2,
  "estimated_tax_savings": 1500.00,
  "estimated_fees": 75.00,
  "estimated_capital_needed": 7500.00
}
```

### 4. Execute Plan (Dry-Run First)
```python
# API call - DRY RUN
POST /api/v1/tlh/plan/execute?dry_run=true

# Returns:
{
  "successful": [...],
  "failed": [],
  "total_tax_savings": 1500.00,
  "total_fees": 75.00
}

# Then execute for real
POST /api/v1/tlh/plan/execute?dry_run=false
```

## Core Classes

### TLHEngine
Main orchestrator - use this for coordinating everything.

```python
from app.services.tlh_engine import TLHEngine

engine = TLHEngine(
    scorer=scorer,
    executor=executor,
    event_listener=listener
)

# Main methods
recommendations = engine.scan_portfolio(positions)
plan = engine.create_execution_plan(rec_ids)
results = await engine.execute_plan(plan, dry_run=True)
```

### TLHScorer
Pure scoring logic - transparent 6-component scoring.

```python
from app.services.tlh_scorer import TLHScorer

score, breakdown = TLHScorer.score_opportunity(
    loss_amount=Decimal("5000"),
    tax_rate=24.0,
    liquidity_score=100,
    volatility=15,
    estimated_fees=Decimal("50"),
    wash_sale_days_remaining=0,
    price_momentum=-3.0
)

explanation = TLHScorer.get_score_explanation(score, breakdown)
print(f"Score: {score}/100 - {explanation}")
```

### TLHExecutor
Order execution with strategies.

```python
from app.services.tlh_executor import TLHExecutor, ImmediateExecutionStrategy

executor = TLHExecutor()

# Dry-run first
dry_result = executor.dry_run(
    asset="BTC",
    quantity=Decimal("1.5"),
    current_price=Decimal("30000")
)

# Real execution
strategy = ImmediateExecutionStrategy(executor)
result = strategy.execute(
    asset="BTC",
    quantity=Decimal("1.5"),
    current_price=Decimal("30000")
)
```

### TLHEventListener
Price monitoring and event triggering.

```python
from app.services.tlh_event_listener import TLHEventListener

listener = TLHEventListener()

# Register assets for monitoring
listener.register_asset("BTC", drop_threshold_pct=5.0)
listener.register_asset("ETH", drop_threshold_pct=5.0)

# Subscribe to events
def on_tlh_event(event):
    print(f"Event: {event.event_type.value}")
    print(f"Price change: {event.price_change_pct:.1f}%")

listener.subscribe(on_tlh_event)

# When price updates arrive
listener.on_price_update("BTC", Decimal("28500"))
```

## Common Workflows

### Workflow 1: Manual Scan & Execute

```python
# 1. Scan for opportunities
recommendations = engine.scan_portfolio(user_positions)

# 2. Filter to user's preference
high_score_recs = [r for r in recommendations if r.priority_score >= 80]

# 3. Show to user (in UI)
for rec in high_score_recs:
    print(f"{rec.asset}: {rec.priority_score}/100 - {rec.explanation}")

# 4. User selects recommendations
selected_ids = ["pos_btc_001"]

# 5. Create execution plan
plan = engine.create_execution_plan(selected_ids)

# 6. Dry-run to show preview
dry_results = engine.execute_plan(plan, dry_run=True)

# 7. User confirms
# (In real UI: wait for user click)

# 8. Execute for real
results = await engine.execute_plan(plan, dry_run=False)

# 9. Show results
print(f"✅ Executed {len(results['successful'])} orders")
```

### Workflow 2: Event-Driven Auto-Execution

```python
# 1. Setup listener
listener = TLHEventListener()
listener.register_asset("BTC", drop_threshold_pct=5.0)

# 2. Subscribe to events
async def on_price_event(event):
    if event.event_type == PriceEventType.PRICE_DROP:
        # Recalculate TLH
        recommendations = engine.scan_portfolio(user_positions)
        
        # Find BTC recommendations
        btc_recs = [r for r in recommendations if r.asset == "BTC"]
        
        if btc_recs and btc_recs[0].priority_score >= 90:
            # Auto-execute
            plan = engine.create_execution_plan([btc_recs[0].position_id])
            results = await engine.execute_plan(plan, dry_run=False)
            print(f"✅ Auto-executed: {btc_recs[0].asset}")

listener.subscribe(on_price_event)

# 3. When price updates arrive (from price feed service)
listener.on_price_update("BTC", new_price)
```

### Workflow 3: Dry-Run Preview for User

```python
# User selects recommendations
selected_ids = ["pos_btc_001", "pos_eth_001"]

# Create plan
plan = engine.create_execution_plan(selected_ids, strategy="immediate")

# Show estimates
print(f"Tax savings: ${plan.estimated_tax_savings:.2f}")
print(f"Fees: ${plan.estimated_fees:.2f}")
print(f"Net benefit: ${plan.estimated_tax_savings - plan.estimated_fees:.2f}")

# Dry-run to show exact preview
dry_results = await engine.execute_plan(plan, dry_run=True)

# Extract results
for rec in plan.recommendations:
    if rec.position_id in [r['position_id'] for r in dry_results['successful']]:
        print(f"Execute {rec.asset}:")
        print(f"  Quantity: 1.5")
        print(f"  Price: $29,950 (with slippage)")
        print(f"  Fees: $50")
        print(f"  Proceeds: $44,875")

# User reviews and confirms

# Now execute for real
real_results = await engine.execute_plan(plan, dry_run=False)
```

## API Endpoints Cheat Sheet

```
SCANNING
POST   /api/v1/tlh/scan                    → Find opportunities

RECOMMENDATIONS
GET    /api/v1/tlh/recommendations         → List all
GET    /api/v1/tlh/recommendations/{id}    → Get specific
POST   /api/v1/tlh/recommendations/{id}/approve  → Approve
POST   /api/v1/tlh/recommendations/{id}/cancel   → Cancel

EXECUTION
POST   /api/v1/tlh/plan/create             → Create plan
POST   /api/v1/tlh/plan/execute            → Execute (dry_run or real)
GET    /api/v1/tlh/history                 → Get history

EVENTS
POST   /api/v1/tlh/events/price-update     → Report price update
POST   /api/v1/tlh/events/register-asset   → Register for monitoring
GET    /api/v1/tlh/events/history          → Get event history
```

## Configuration

### Set in tlh_engine.py:

```python
# Auto-execute if score >= this
TLH_ENGINE.auto_execute_min_score = 90

# Allow auto-execution at all
TLH_ENGINE.allow_auto_execution = True

# In TLHEventListener:
listener.thresholds['BTC'].event_cooldown_seconds = 300  # 5 min cooldown

# In ExecutionPlan:
plan = engine.create_execution_plan(ids, strategy="immediate")
# strategy can be: "immediate", "limit_price", "scheduled"
```

## Testing

### Unit Test Example
```python
def test_scoring():
    score, breakdown = TLHScorer.score_opportunity(
        loss_amount=Decimal("5000"),
        tax_rate=24.0,
        liquidity_score=100,
        volatility=15,
        estimated_fees=Decimal("50"),
        wash_sale_days_remaining=0,
        price_momentum=-3.0
    )
    
    assert score > 80
    assert 'tax_savings_component' in breakdown
    assert breakdown['total_score'] == score

def test_dry_run():
    executor = TLHExecutor()
    result = executor.dry_run(
        asset="BTC",
        quantity=Decimal("1.5"),
        current_price=Decimal("30000")
    )
    
    assert result.successful
    assert result.order_id.startswith('DRY_')

def test_event_listener():
    listener = TLHEventListener()
    listener.register_asset("BTC", drop_threshold_pct=5.0)
    
    # Initial price
    listener.on_price_update("BTC", Decimal("30000"))
    
    # 5% drop
    event = listener.on_price_update("BTC", Decimal("28500"))
    
    assert event is not None
    assert event.event_type == PriceEventType.PRICE_DROP
    assert event.price_change_pct < -5
```

### Integration Test Example
```python
async def test_complete_flow():
    # Setup
    engine = TLHEngine(
        scorer=TLHScorer(),
        executor=TLHExecutor(),
        event_listener=TLHEventListener()
    )
    
    positions = [
        {
            'id': 'pos_btc_001',
            'asset': 'BTC',
            'quantity': Decimal('1.5'),
            'average_cost': Decimal('35000'),
            'current_price': Decimal('30000'),
            'purchase_date': datetime.now() - timedelta(days=180),
            'exchanges': ['binance']
        }
    ]
    
    # Flow
    recommendations = engine.scan_portfolio(positions)
    assert len(recommendations) > 0
    
    plan = engine.create_execution_plan([r.position_id for r in recommendations])
    assert plan.estimated_tax_savings > 0
    
    results = await engine.execute_plan(plan, dry_run=True)
    assert len(results['successful']) > 0
```

## Debugging Tips

### Q: Score is too high/low?
A: Check 6 components in breakdown dict
```python
score, breakdown = TLHScorer.score_opportunity(...)
for component, value in breakdown.items():
    print(f"  {component}: {value}")
```

### Q: Event not triggering?
A: Check cooldown and threshold
```python
threshold = listener.thresholds["BTC"]
print(f"  Last event: {threshold.last_event_time}")
print(f"  Drop threshold: {threshold.drop_threshold_pct}%")
print(f"  Last price: {threshold.last_price}")
```

### Q: Dry-run shows high fees?
A: Check market impact calculation in executor
```python
result = executor.dry_run(asset, quantity, price)
print(f"  Slippage: {result.slippage}%")
print(f"  Fees: ${result.fees_paid}")
```

### Q: Recommendation expired?
A: Check expiry time
```python
rec = engine.recommendations.get(position_id)
if rec.is_expired():
    print("Recommendation expired, need to rescan portfolio")
    engine.cancel_recommendation(position_id)
```

## Performance Tips

1. **Batch scan**: Scan all positions at once (not one-by-one)
2. **Cache prices**: Don't fetch prices repeatedly
3. **Async execution**: Use async/await for I/O operations
4. **Event cooldown**: Prevents spam (default 5 min)
5. **Limit history**: Keep only last 1000 events

```python
# Good: Batch operation
positions = await db.get_all_positions(user_id)
recs = engine.scan_portfolio(positions)  # 50ms for 100 positions

# Bad: One-by-one
for pos in positions:
    recs = engine.scan_portfolio([pos])  # 50ms × 100 = 5 seconds!
```

## Production Checklist

- [ ] Database models created + migrated
- [ ] Price feed connected to on_price_update() API
- [ ] Portfolio data connected to scan_portfolio()
- [ ] Authentication added (verify user owns positions)
- [ ] Error handling + logging added
- [ ] Rate limiting implemented
- [ ] Dry-run required before real execution
- [ ] Monitoring + alerts configured
- [ ] Tests pass + coverage > 80%
- [ ] Documentation for operations team

---

Great! That's everything you need to get started. Happy TLH engine building! 🚀
