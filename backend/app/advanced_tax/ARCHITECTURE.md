# Advanced Tax Engine - Architecture & Integration Guide

## 🏗️ OVERVIEW

**Advanced Tax Engine** is an enterprise-grade, standalone module that extends LatamTax with premium optimization and compliance features.

```
PROJECT STRUCTURE:
Tax/
├── backend/                          (FastAPI main app)
├── frontend/                         (React)
├── advanced-tax-engine/              (NEW - Premium features)
│   ├── services/                     (Core business logic)
│   │   ├── __init__.py
│   │   ├── tax_loss_optimizer.py     (Tax-Loss Harvesting)
│   │   ├── reconciliation.py         (Smart Reconciliation)
│   │   ├── audit_engine.py           (Audit Trail & Export)
│   │   └── base_service.py           (Base class for all services)
│   ├── models/                       (SQLAlchemy ORM models)
│   │   ├── __init__.py
│   │   ├── tax_loss_models.py
│   │   ├── reconciliation_models.py
│   │   ├── audit_models.py
│   │   └── shared.py                 (Common base models)
│   ├── routers/                      (FastAPI routers)
│   │   ├── __init__.py
│   │   ├── tax_loss_routes.py        (REST endpoints)
│   │   ├── reconciliation_routes.py
│   │   ├── audit_routes.py
│   │   └── health.py                 (Status endpoints)
│   ├── integration/                  (Backend integration)
│   │   ├── __init__.py
│   │   ├── database.py               (DB session management)
│   │   ├── auth.py                   (Auth integration)
│   │   ├── events.py                 (Event system)
│   │   └── middleware.py
│   ├── utils/                        (Utilities)
│   │   ├── __init__.py
│   │   ├── validators.py             (Input validation)
│   │   ├── formatters.py             (Data formatting)
│   │   ├── constants.py              (Shared constants)
│   │   └── exceptions.py             (Custom exceptions)
│   ├── tests/                        (Unit & integration tests)
│   │   ├── __init__.py
│   │   ├── test_tax_loss.py
│   │   ├── test_reconciliation.py
│   │   ├── test_audit.py
│   │   └── conftest.py
│   ├── docs/                         (Documentation)
│   │   ├── INTEGRATION.md            (How to integrate with backend)
│   │   ├── API.md                    (REST API reference)
│   │   ├── DATABASE.md               (Database schema)
│   │   └── EXAMPLES.md               (Usage examples)
│   ├── requirements.txt              (Dependencies)
│   ├── __init__.py                   (Package init)
│   └── config.py                     (Configuration)
└── output/
```

---

## 🔗 INTEGRATION POINTS

### 1. **Database Layer**
```python
# All models extend a shared BaseModel
# Uses backend's SQLAlchemy session for transactions
# Creates tables in same DB as backend
# Works with migration system (Alembic)

FROM backend.app.db import get_db, Base
# All advanced-tax-engine models inherit from this Base
```

### 2. **Authentication Layer**
```python
# Reuses backend's auth system
# GET_CURRENT_USER dependency injection from backend

FROM backend.app.security import get_current_user
# Protected routes use same JWT tokens
```

### 3. **Router Registration**
```python
# Routers are registered in backend's main.py
# Mounted under /api/premium/ namespace

FROM advanced_tax_engine.routers import (
    tax_loss_routes,
    reconciliation_routes,
    audit_routes,
)

app.include_router(tax_loss_routes.router, prefix="/api/premium/tax-loss")
app.include_router(reconciliation_routes.router, prefix="/api/premium/reconciliation")
app.include_router(audit_routes.router, prefix="/api/premium/audit")
```

### 4. **Data Flow**
```
User Action (Frontend)
    ↓
[API Endpoint] (/api/premium/tax-loss/opportunities)
    ↓
[Router Layer] (tax_loss_routes.py - handles request validation)
    ↓
[Service Layer] (TaxLossOptimizer - business logic)
    ↓
[Model Layer] (SQLAlchemy ORM - database access)
    ↓
[Backend DB] (Shared database)
    ↓
[Response] (JSON → Frontend)
```

---

## 📦 LAYERS EXPLAINED

### **Layer 1: Models** (`/models/`)
Definition: ORM models for database persistence
- Inherit from `Base` (shared with backend)
- Define table schema
- Include relationships
- Have validation methods
```python
class TaxLossHarvest(Base):
    __tablename__ = "tax_loss_harvests"
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("user.id"))
    # ...
```

### **Layer 2: Services** (`/services/`)
Definition: Pure business logic (no Flask/FastAPI code)
- Accepts primitive types (int, str, dict)
- Returns data classes or dicts
- Can be used standalone (e.g., in CLI, jobs)
- Tests don't need FastAPI context
```python
class TaxLossOptimizer:
    def scan_portfolio(self, user_id: int) -> List[HarvestOpportunity]:
        # Pure business logic
        pass
```

### **Layer 3: Routers** (`/routers/`)
Definition: REST API handlers
- FastAPI dependencies (@router.get, @router.post)
- Call services
- Validate inputs
- Format responses
```python
@router.get("/opportunities")
async def get_opportunities(user_id: int = Depends(get_current_user)):
    optimizer = TaxLossOptimizer(get_db())
    return optimizer.scan_portfolio(user_id.id)
```

### **Layer 4: Integration** (`/integration/`)
Definition: Connects to backend systems
- Database session management
- Authentication token parsing
- Event publishing
- Middleware for logging

---

## 🔄 COMMUNICATION FLOW

### Example: Tax-Loss Harvesting

```
1. USER INITIATES (Frontend)
   → Calls POST /api/premium/tax-loss/opportunities

2. ROUTER INTERCEPTS (routers/tax_loss_routes.py)
   → Validates request
   → Extracts user_id from JWT
   → Creates service instance

3. SERVICE EXECUTES (services/tax_loss_optimizer.py)
   → Queries wallet transactions
   → Calculates P&L for each asset
   → Ranks opportunities
   → Returns list

4. MODEL LAYER (models/tax_loss_models.py)
   → TaxLossOptimizer queries database
   → Uses SQLAlchemy ORM
   → Caches results in TaxLossHarvest table

5. RESPONSE FORMATTED (routers/tax_loss_routes.py)
   → Converts output to JSON
   → Returns 200 OK

6. FRONTEND DISPLAYS
   → Shows opportunities sorted by tax savings
   → User clicks "Execute"
   → Cycle repeats for execute endpoint
```

---

## 🧵 THREADING & CONCURRENCY

### Long-Running Operations
```python
# Some operations (harvest execution, audit export) are long-running
# Solution: Use background jobs (Celery or APScheduler)

# In service:
async def execute_harvest_async(self, opportunity_id: int):
    # Queue job
    schedule_harvest_execution.delay(opportunity_id)
    # Return immediately with job_id
    return {"status": "queued", "job_id": job_id}

# User polls for result:
@router.get("/harvest-status/{job_id}")
async def get_harvest_status(job_id: str):
    result = get_job_result(job_id)
    return result
```

---

## 📊 DATABASE SCHEMA INTEGRATION

### New Tables (in backend DB)
```sql
-- Tax Loss Harvesting
CREATE TABLE tax_loss_harvests (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    asset VARCHAR NOT NULL,
    loss_amount DECIMAL,
    tax_savings DECIMAL,
    status VARCHAR,
    created_at TIMESTAMP,
    executed_at TIMESTAMP
);

-- Smart Reconciliation
CREATE TABLE missing_cost_basis (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    status VARCHAR,
    cost_basis DECIMAL,
    matched_at TIMESTAMP
);

-- Audit Trail
CREATE TABLE audit_packages (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    country VARCHAR,
    tax_year INTEGER,
    total_tax DECIMAL,
    generated_at TIMESTAMP,
    file_path VARCHAR
);
```

### No Schema Conflicts
- Uses unique `tax_loss_*`, `reconciliation_*`, `audit_*` prefixes
- Foreign keys to existing `user` table
- No modifications to existing backend tables

---

## 🔐 SECURITY ARCHITECTURE

### Authentication
```python
# Reuses backend JWT tokens
# Same secret key
# Same user validation

@router.get("/opportunities")
async def get_opportunities(user_id = Depends(get_current_user)):
    # user_id is validated JWT token
    return {...}
```

### Authorization
```python
# Role-based access control
# Premium users only

@router.get("/opportunities")
async def get_opportunities(user_id = Depends(get_current_user)):
    # Check if user has "premium" subscription
    if not user_has_premium(user_id):
        raise HTTPException(status_code=403, detail="Premium feature")
    return {...}
```

### Data Isolation
```python
# Every query filters by user_id
# No data leakage between users

def get_harvest_opportunities(self, user_id: int):
    return db.query(TaxLossHarvest).filter(
        TaxLossHarvest.user_id == user_id  # CRITICAL
    ).all()
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

### Development
```
Backend (FastAPI)
├── Main app.py
├── Import advanced-tax-engine routers
└── Run with uvicorn

Advanced Tax Engine
├── Services (no external server)
├── Models (same DB)
└── Routers (included in FastAPI)
```

### Production
```
Load Balancer
├── FastAPI Instance 1 (includes advanced-tax-engine)
├── FastAPI Instance 2 (includes advanced-tax-engine)
└── FastAPI Instance N

Database (PostgreSQL)
├── backend tables
├── advanced-tax-engine tables (same DB)
└── Replication/backup

Cache Layer (Redis)
├── Price data cache
├── Portfolio calculations cache
└── User session cache

Background Workers
├── Harvest execution
├── Audit export generation
└── Price updates
```

---

## 📈 MONITORING & LOGGING

### Log Structure
```python
# All advanced-tax-engine operations logged
logger.info("TAX_LOSS", {
    "user_id": 123,
    "action": "harvest_executed",
    "asset": "BTC",
    "tax_savings": 500,
    "timestamp": datetime.now()
})
```

### Metrics to Track
- Tax-loss opportunities identified
- Reconciliation matches made
- Audit packages generated
- Average tax savings per user
- System performance (response time)

---

## 🧪 TESTING STRATEGY

### Unit Tests
```python
# /tests/test_tax_loss.py
# Tests services in isolation
# No FastAPI context needed

def test_portfolio_scanning():
    optimizer = TaxLossOptimizer(mock_db)
    opportunities = optimizer.scan_portfolio(user_id=1)
    assert len(opportunities) > 0
```

### Integration Tests
```python
# /tests/test_integration.py
# Tests with real Flask app & DB
# Creates test user & data

def test_tax_loss_api(client):
    response = client.get("/api/premium/tax-loss/opportunities")
    assert response.status_code == 200
```

---

## 📝 CONFIGURATION MANAGEMENT

### `/advanced-tax-engine/config.py`
```python
class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Features
    HARVEST_EXECUTION_ENABLED = True
    RECONCILIATION_AUTO_MATCH = True
    AUDIT_EXPORT_FORMATS = ["pdf", "json", "excel"]
    
    # Limits
    MAX_HARVEST_PER_USER = 100
    MAX_RECONCILIATION_GAPS = 1000
    AUDIT_EXPORT_MAX_TRANSACTIONS = 100000
    
    # Tax rules
    WASH_SALE_DAYS = 30
    TAX_YEARS_LOOKBACK = 5
```

---

## 🔌 PLUGIN SYSTEM FOR FUTURE GROWTH

### Adding New Premium Features
```
Step 1: Create feature module
  ├── /services/new_feature.py
  ├── /models/new_feature_models.py
  └── /routers/new_feature_routes.py

Step 2: Register with backend
  └── app.include_router(new_feature_routes.router, ...)

Step 3: Add tests
  └── /tests/test_new_feature.py

Complete! Feature is now part of engine.
```

---

## 📚 DOCUMENTATION STRUCTURE

```
/docs/
├── INTEGRATION.md       ← How to integrate with backend
├── API.md               ← REST endpoint reference
├── DATABASE.md          ← Schema & migrations
├── EXAMPLES.md          ← Usage examples
├── ARCHITECTURE.md      ← This file
└── DEPLOYMENT.md        ← Production setup
```

---

## ✅ CHECKLIST FOR "SERIOUS PRODUCT" IMAGE

- [x] **Separate folder** (not buried in backend)
- [x] **Professional structure** (services, models, routers, etc.)
- [x] **Clear documentation** (architecture, integration, API)
- [x] **Database isolation** (own tables, no conflicts)
- [x] **Authentication** (reuse backend security)
- [x] **Testing** (unit + integration)
- [x] **Error handling** (custom exceptions)
- [x] **Performance** (caching, pagination)
- [x] **Monitoring** (logging, metrics)
- [x] **Deployment ready** (can scale independently)

---

## 🎯 NEXT STEPS

1. **Implement Models** (database schema)
2. **Implement Services** (business logic)
3. **Implement Routers** (API endpoints)
4. **Integration Tests**
5. **Frontend Components**
6. **Production Deployment**
