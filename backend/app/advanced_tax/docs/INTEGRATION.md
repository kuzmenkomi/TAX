# Advanced Tax Engine - Backend Integration Guide

## 🔌 QUICK INTEGRATION (5 minutes)

### Step 1: Import Routers in Backend (backend/app/main.py)

```python
# Add imports at top
from advanced_tax_engine.routers import (
    tax_loss_routes,
    reconciliation_routes,
    audit_routes,
)

# In FastAPI app creation (after other routers):
# Include Advanced Tax Engine routers
app.include_router(
    tax_loss_routes.router,
    prefix="/api/premium/tax-loss",
    tags=["premium-tax-loss"]
)

app.include_router(
    reconciliation_routes.router,
    prefix="/api/premium/reconciliation",
    tags=["premium-reconciliation"]
)

app.include_router(
    audit_routes.router,
    prefix="/api/premium/audit",
    tags=["premium-audit"]
)
```

### Step 2: Initialize Database (backend/app/db.py)

```python
# Add to db.py
from advanced_tax_engine.integration.database import init_db as init_premium_db

def init_all_databases():
    """Initialize all databases"""
    # Backend tables
    Base.metadata.create_all(bind=engine)
    
    # Advanced Tax Engine tables
    init_premium_db()

# Call on startup
init_all_databases()
```

### Step 3: Update Backend Dependencies

Add to `backend/requirements.txt`:
```
# Advanced Tax Engine dependencies
-r ../advanced-tax-engine/requirements.txt
```

Or manually add these key dependencies:
```
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

### Step 4: Test Integration

```bash
# From Tax/ directory (root)
cd backend
python -c "from advanced_tax_engine.routers import tax_loss_routes; print('✓ Import successful')"

# Run backend test
pytest tests/ -v
```

---

## 🔐 AUTHENTICATION INTEGRATION

### Current: Stub User ID

All endpoints currently use `user_id = 1` (stub).

### Integration: Use JWT Token

**Option 1: Extract from Existing Backend JWT**

```python
# In advanced-tax-engine/integration/auth.py

from fastapi import Depends, HTTPException
from backend.app.security import get_current_user  # Import from backend

async def get_premium_user(current_user = Depends(get_current_user)):
    """Get current user for premium features"""
    if not hasattr(current_user, 'id'):
        raise HTTPException(status_code=401, detail="Invalid token")
    return current_user

# Then in routers:
async def get_opportunities(
    db: Session = Depends(get_db),
    user = Depends(get_premium_user),  # Use this instead of stub
):
    optimizer = TaxLossOptimizer(db, user.id)
    return optimizer.scan_portfolio()
```

**Option 2: Create Premium User Middleware**

```python
# In advanced-tax-engine/integration/middleware.py

from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthcredentials

bearer_scheme = HTTPBearer()

async def get_current_premium_user(credentials: HTTPAuthCredentials = Depends(bearer_scheme)):
    """Validate JWT and extract user"""
    token = credentials.credentials
    
    # Validate token (reuse backend logic)
    from backend.app.security import verify_token
    
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401)
    
    return {"user_id": int(user_id)}
```

---

## 💾 DATABASE INTEGRATION

### Shared Database Setup

**Option 1: Same PostgreSQL (Recommended for Production)**

```python
# advanced-tax-engine/config.py
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/latamtax"
)

# This is the SAME database as backend
# Both backend and advanced-tax-engine use it
```

**Option 2: SQLite (Development)**

```python
# SQLite doesn't support locks well
# Each service gets own file:

BACKEND_DB = "sqlite:///./backend.db"
PREMIUM_DB = "sqlite:///./premium.db"

# OR use same file for simplicity:
SHARED_DB = "sqlite:///./tax.db"  # Both use this
```

### No Schema Conflicts

All Advanced Tax Engine tables use prefixes:
- `tax_loss_*` - Tax-loss harvesting tables
- `reconciliation_*` - Smart reconciliation
- `audit_*` - Audit trail

No modifications to existing backend tables.

### Migrations

```bash
# Advanced Tax Engine uses Alembic (like backend)

cd advanced-tax-engine

# Create migration
alembic revision --autogenerate -m "Add tax loss tables"

# Apply migration
alembic upgrade head
```

---

## 🔗 DATA FLOW EXAMPLES

### Example 1: Tax-Loss Harvesting

```
Frontend Call:
  GET /api/premium/tax-loss/opportunities

Router (tax_loss_routes.py):
  1. Validates JWT token
  2. Extracts user_id
  3. Gets database session
  4. Creates TaxLossOptimizer

TaxLossOptimizer (tax_loss_optimizer.py):
  1. Queries user wallets from backend
  2. Queries user exchanges from backend
  3. Calculates positions
  4. Finds losses
  5. Ranks by tax savings
  6. Saves to tax_loss_harvests table

Response:
  {
    "opportunities": [
      {"asset": "BTC", "loss": 2000, "tax_savings": 600}
    ]
  }
```

### Example 2: Smart Reconciliation

```
User Has:
  - Wallet with "5 ETH received 2024-01-15"
  - No record of where ETH came from
  - System sees gap (missing cost basis)

Reconciliation Scan:
  1. Detects gap
  2. Searches for source transaction
  3. Finds "Sold 5 ETH on Coinbase 2024-01-14"
  4. Links them (API call, timestamp, qty match)
  5. Proposes: "Cost basis = $10,000 (exchange price)"

User Action:
  - Click "Accept Match"
  - Cost basis is now set
  - Gap is resolved

Database:
  - missing_cost_basis.matched = True
  - reconciliation_matches.send_txn = Coinbase sell
  - reconciliation_matches.receive_txn = Wallet receive
```

### Example 3: Audit Export

```
Tax Year: 2024
User Requests: "Export audit package"

Audit Engine:
  1. Queries all transactions for 2024
  2. Gets all tax calculations for 2024
  3. Collects all rules used
  4. Generates:
     - JSON (machine-readable)
     - PDF (professional report)
     - Excel (for further analysis)
  5. Signs and timestamps files
  6. Saves to audit_packages table

Response:
  {
    "package_id": 789,
    "transaction_count": 500,
    "total_tax": 25000,
    "files": {
      "json": "/audit/download/789/json",
      "pdf": "/audit/download/789/pdf"
    }
  }
```

---

## 🧪 TESTING INTEGRATION

### Unit Tests (No Backend Needed)

```bash
cd advanced-tax-engine
pytest tests/test_tax_loss.py -v
# Tests TaxLossOptimizer in isolation
```

### Integration Tests (With Backend)

```bash
cd backend
pytest tests/test_premium_integration.py -v
# Tests full flow: API → Router → Service → DB
```

### Example Integration Test

```python
# backend/tests/test_premium_integration.py

def test_tax_loss_api(client):
    """Test tax-loss endpoint through FastAPI"""
    response = client.get("/api/premium/tax-loss/opportunities?country=MX")
    
    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert data["status"] == "success"
```

---

## 🚀 DEPLOYMENT STRATEGY

### Development
```
Single FastAPI instance
  ├── Backend routes
  ├── Advanced Tax Engine routers (included)
  └── SQLite database
```

### Production
```
Load Balancer
  ├── FastAPI Instance 1 (with premium features)
  ├── FastAPI Instance 2 (with premium features)
  └── FastAPI Instance N

PostgreSQL (shared)
  ├── Backend tables
  ├── Tax-loss tables
  ├── Reconciliation tables
  ├── Audit tables
  └── Automatic backups

Redis Cache
  └── Price data, user sessions, calculations
```

### Environment Variables

```bash
# .env or production config

# Database
DATABASE_URL=postgresql://user:pass@db:5432/latamtax

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# Advanced Tax Engine
ATX_LOG_LEVEL=INFO
ATX_AUTO_EXECUTE=false        # Manual execution
ATX_MAX_HARVEST=100
ATX_WASH_SALE_DAYS=30

# Features
ATX_TAX_LOSS_ENABLED=true
ATX_RECONCILIATION_ENABLED=true
ATX_AUDIT_TRAIL_ENABLED=true
```

---

## 🔍 MONITORING & LOGGING

### Structured Logging

All Advanced Tax Engine operations log to:

```
[ADVANCED_TAX_ENGINE] Tax-Loss Optimizer: PORTFOLIO_SCAN_STARTED
[ADVANCED_TAX_ENGINE] Reconciliation Engine: GAP_SCAN_COMPLETE
[ADVANCED_TAX_ENGINE] Audit Engine: AUDIT_GENERATION_FAILED
```

### Key Metrics to Track

```python
# In production monitoring system (DataDog, New Relic, etc.)

metrics = {
    "tax_loss.opportunities_identified": 245,
    "tax_loss.total_savings": 12500.00,
    "reconciliation.gaps_found": 1200,
    "reconciliation.auto_matches": 890,
    "audit.packages_generated": 45,
    "audit.exports_downloaded": 28,
}
```

---

## ❌ TROUBLESHOOTING

### Issue: Import Error
```
ImportError: cannot import name 'advanced_tax_engine'
```

**Solution:** Ensure `advanced-tax-engine` folder is in Python path
```python
import sys
sys.path.insert(0, '/path/to/Tax')  # Root directory
```

### Issue: Database Tables Not Created
```
ProgrammingError: relation "tax_loss_harvests" does not exist
```

**Solution:** Run migrations
```bash
cd advanced-tax-engine
alembic upgrade head
```

### Issue: JWT Token Not Found
```
HTTPException: 401 Unauthorized - Invalid token
```

**Solution:** Include Bearer token in request
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/premium/tax-loss/opportunities
```

---

## ✅ INTEGRATION CHECKLIST

- [ ] Routers imported in backend/app/main.py
- [ ] Database initialized with advanced-tax-engine tables
- [ ] Dependencies installed (requirements.txt)
- [ ] JWT authentication working
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Environment variables configured
- [ ] Logging configured
- [ ] Frontend connected to new API endpoints
- [ ] Premium feature flag enabled
- [ ] Documentation updated
- [ ] Deployment ready

---

## 📞 SUPPORT

For issues or questions:
1. Check logs in `/tmp/advanced-tax-engine.log`
2. Run tests: `pytest tests/ -v --tb=short`
3. Debug with: `python -c "from advanced_tax_engine import Config; print(Config)"`
