# 🔌 TAX-LOSS HARVESTING - BACKEND INTEGRATION GUIDE

## 🚀 БЫСТРАЯ ИНТЕГРАЦИЯ (5 минут)

### Шаг 1: Добавить routers в main.py

```python
# backend/app/main.py

from fastapi import FastAPI
from advanced_tax_engine.routers import tax_loss_routes
from advanced_tax_engine.integration.database import init_db, SessionLocal

app = FastAPI()

# Инициализировать DB
@app.on_event("startup")
async def startup():
    init_db()

# Регистрировать routes
app.include_router(
    tax_loss_routes.router,
    prefix="/api/v1/tax-loss",
    tags=["tax-loss-harvesting"]
)
```

### Шаг 2: Запустить сервер

```bash
cd backend
uvicorn app.main:app --reload
```

### Шаг 3: Тестировать endpoints

```bash
# Сканировать портфель
curl -X GET "http://localhost:8000/api/v1/tax-loss/opportunities" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Выполнить harvest
curl -X POST "http://localhost:8000/api/v1/tax-loss/execute/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📡 API ENDPOINTS

### 1. Сканировать портфель

```http
GET /api/v1/tax-loss/opportunities
```

**Response:**
```json
{
  "opportunities": [
    {
      "id": 1,
      "asset": "BTC",
      "quantity": 1.5,
      "purchase_price": 45000,
      "current_price": 30000,
      "loss_amount": 22500,
      "loss_percentage": -33.3,
      "tax_savings": 5400,
      "estimated_fees": 45,
      "net_benefit": 5355,
      "cost_basis_method": "LIFO",
      "wash_sale_days_remaining": 0,
      "liquidity_score": 100,
      "volatility": 8.5,
      "risk_level": "low",
      "priority_score": 95,
      "status": "identified",
      "rebuy_suggestion": "ETH",
      "can_harvest": true
    },
    {
      "id": 2,
      "asset": "ETH",
      "quantity": 5,
      "loss_amount": 8000,
      "tax_savings": 1920,
      "net_benefit": 1900,
      "priority_score": 87,
      ...
    }
  ],
  "summary": {
    "total_opportunities": 2,
    "total_loss": 30500,
    "total_tax_savings": 7320,
    "total_fees": 100,
    "net_benefit": 7220,
    "average_priority": 91
  }
}
```

---

### 2. Получить summary

```http
GET /api/v1/tax-loss/impact-summary
```

**Response:**
```json
{
  "total_opportunities": 5,
  "total_loss_amount": 50000,
  "total_tax_savings": 12000,
  "total_estimated_fees": 150,
  "net_benefit": 11850,
  "average_priority": 88.5
}
```

---

### 3. Выполнить harvest

```http
POST /api/v1/tax-loss/execute/{opportunity_id}

{
  "confirm": true,
  "notes": "Manual harvest for BTC"
}
```

**Response:**
```json
{
  "status": "executed",
  "harvest_id": 1,
  "asset": "BTC",
  "quantity": 1.5,
  "executed_price": 30000,
  "tax_savings": 5400,
  "rebuy_date": "2024-02-10",
  "rebuy_suggestion": "ETH",
  "transaction_hash": "0x123..."
}
```

---

### 4. Выполнить rebuy

```http
POST /api/v1/tax-loss/execute-rebuy/{harvest_id}

{
  "rebuy_asset": "ETH",
  "quantity": 0.3,
  "confirm": true
}
```

**Response:**
```json
{
  "status": "rebuy_scheduled",
  "harvest_id": 1,
  "original_asset": "BTC",
  "rebuy_asset": "ETH",
  "rebuy_quantity": 0.3,
  "rebuy_scheduled_date": "2024-02-10"
}
```

---

### 5. История harvests

```http
GET /api/v1/tax-loss/history?asset=BTC&status=executed&year=2024
```

**Response:**
```json
{
  "harvests": [
    {
      "id": 1,
      "asset": "BTC",
      "executed_date": "2024-01-15",
      "quantity": 1.5,
      "executed_price": 30000,
      "tax_savings": 5400,
      "status": "completed",
      "rebuy_asset": "ETH",
      "rebuy_date": "2024-02-10"
    }
  ],
  "total_count": 3,
  "total_tax_savings_this_year": 15600
}
```

---

### 6. Статус harvest

```http
GET /api/v1/tax-loss/status/{harvest_id}
```

**Response:**
```json
{
  "harvest_id": 1,
  "asset": "BTC",
  "status": "executed",
  "created_at": "2024-01-10",
  "executed_at": "2024-01-12",
  "executed_price": 30000,
  "tax_savings": 5400,
  "wash_sale_period_ends": "2024-02-11",
  "rebuy_suggestion": "ETH",
  "rebuy_scheduled_at": "2024-02-10",
  "rebuy_executed_at": null
}
```

---

## 🔐 AUTHENTICATION

Все endpoints требуют JWT token:

```python
# Middleware validates token & extracts user_id
@app.get("/api/v1/tax-loss/opportunities")
async def get_opportunities(
    request: Request,
    db: Session = Depends(get_db)
):
    # JWT middleware already validated
    user_id = request.state.user_id  # From JWT
    country = request.state.user.country  # From DB
    
    optimizer = TaxLossOptimizer(db, user_id, country)
    return optimizer.scan_portfolio()
```

---

## 💾 DATABASE CONNECTION

### SQLite (Development)

```python
# advanced_tax_engine/config.py
DATABASE_URL = "sqlite:///./advanced_tax_engine.db"

# Or set env var:
# DATABASE_URL=sqlite:///tax_loss.db python -m uvicorn app.main:app
```

### PostgreSQL (Production)

```python
# advanced_tax_engine/config.py
DATABASE_URL = "postgresql://user:pass@localhost/tax_loss_db"

# Or set env var:
# DATABASE_URL=postgresql://user:pass@localhost/tax_loss_db
```

---

## 🧪 TESTING WITH CURL

### 1. Сканировать все opportunities

```bash
curl -X GET "http://localhost:8000/api/v1/tax-loss/opportunities" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### 2. Выполнить harvest

```bash
curl -X POST "http://localhost:8000/api/v1/tax-loss/execute/1" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "notes": "Manual harvest"
  }'
```

### 3. Проверить статус

```bash
curl -X GET "http://localhost:8000/api/v1/tax-loss/status/1" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 🧬 PYTHON CLIENT EXAMPLE

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/tax-loss"
JWT_TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Get opportunities
response = requests.get(f"{BASE_URL}/opportunities", headers=headers)
opportunities = response.json()

print(f"Found {len(opportunities['opportunities'])} opportunities")
print(f"Total tax savings: ${opportunities['summary']['total_tax_savings']}")

# 2. Execute harvest
opp_id = opportunities['opportunities'][0]['id']
execute_response = requests.post(
    f"{BASE_URL}/execute/{opp_id}",
    headers=headers,
    json={"confirm": True}
)

print(f"Harvest executed: {execute_response.json()}")

# 3. Schedule rebuy
harvest_id = execute_response.json()['harvest_id']
rebuy_response = requests.post(
    f"{BASE_URL}/execute-rebuy/{harvest_id}",
    headers=headers,
    json={
        "rebuy_asset": "ETH",
        "quantity": 0.3,
        "confirm": True
    }
)

print(f"Rebuy scheduled: {rebuy_response.json()}")

# 4. Check history
history_response = requests.get(
    f"{BASE_URL}/history",
    headers=headers,
    params={"year": 2024}
)

print(f"Total tax savings this year: ${history_response.json()['total_tax_savings_this_year']}")
```

---

## 🔄 WORKFLOW EXAMPLE

### User Journey:

```
1️⃣ User logs in
   ↓
2️⃣ Frontend calls GET /opportunities
   ↓
3️⃣ Backend scans portfolio:
   - Fetch all positions from transactions
   - Calculate losses for each asset
   - Check wash-sale rules per country
   - Assess liquidity
   - Calculate tax benefits
   - Sort by priority
   ↓
4️⃣ Frontend displays opportunities
   - Show top 5 ranked by priority
   - Display tax savings vs fees
   - Show wash-sale warnings if any
   - Show liquidity warnings if any
   ↓
5️⃣ User clicks "Execute Harvest"
   ↓
6️⃣ Frontend calls POST /execute/{id}
   ↓
7️⃣ Backend:
   - Verify can harvest (no wash-sale conflict)
   - Create SELL action record
   - Mark harvest as EXECUTING
   - In production: send to exchange API
   ↓
8️⃣ Frontend shows confirmation
   - Asset: BTC
   - Quantity: 1.5
   - Tax savings: $1,200
   - Rebuy suggestion: ETH
   - Rebuy date: 2024-02-11
   ↓
9️⃣ User optionally schedules rebuy
   - POST /execute-rebuy with rebuy_asset & quantity
   ↓
🔟 System automatically:
   - Track rebuy date (30-day rule for USA)
   - Suggest rebuy when period ends
   - Notify user when rebuy date arrives
```

---

## 🐛 ERROR HANDLING

### Common errors:

```json
{
  "status": "error",
  "code": "WASH_SALE_VIOLATION",
  "message": "Cannot harvest BTC: 15 days of wash-sale period remaining",
  "data": {
    "days_remaining": 15,
    "eligible_date": "2024-02-10"
  }
}
```

```json
{
  "status": "error",
  "code": "ILLIQUID_ASSET",
  "message": "Cannot harvest SHITCOIN: liquidity score too low (15/100)",
  "data": {
    "liquidity_score": 15,
    "min_required": 30
  }
}
```

```json
{
  "status": "error",
  "code": "FEES_EXCEED_BENEFIT",
  "message": "Cannot sell: estimated fees ($50) exceed tax benefit ($30)",
  "data": {
    "tax_benefit": 30,
    "estimated_fees": 50,
    "net_benefit": -20
  }
}
```

---

## 📊 MONITORING

### Structured logging:

```python
# Every operation is logged
logger.info(f"[TLH] Portfolio scan started for user {user_id}, country {country}")
logger.info(f"[TLH] Found {len(positions)} positions")
logger.info(f"[TLH] Evaluating {asset}...")
logger.info(f"[TLH] {asset} ✓ Opportunity: ${tax_benefit:.2f} tax, priority {priority_score:.1f}")
logger.info(f"[TLH] Found {len(opportunities)} opportunities")

# Errors logged with full context
logger.error(f"Error evaluating {asset}: {str(e)}")
logger.warning(f"Error getting positions: {str(e)}")
```

---

## 🚢 DEPLOYMENT

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
COPY advanced-tax-engine/ /app/advanced_tax_engine/

ENV DATABASE_URL=postgresql://user:pass@postgres:5432/tax_loss

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Development
DATABASE_URL=sqlite:///tax_loss.db
ENVIRONMENT=development
DEBUG=true

# Production
DATABASE_URL=postgresql://user:pass@prod-db:5432/tax_loss
ENVIRONMENT=production
DEBUG=false
JWT_SECRET=your-secret-key
```

---

## 📈 PERFORMANCE OPTIMIZATION

### Database Indexes

All key fields are indexed:
```sql
CREATE INDEX ix_tax_loss_harvests_user_country ON tax_loss_harvests(user_id, country);
CREATE INDEX ix_tax_loss_harvests_status ON tax_loss_harvests(status);
CREATE INDEX ix_missing_cost_basis_user ON missing_cost_basis(user_id, resolved);
CREATE INDEX ix_calculation_audit_user_year ON calculation_audit_records(user_id, created_at);
```

### Caching

```python
# Cache opportunity scan results for 5 minutes
@app.get("/opportunities")
@cache.cached(timeout=300)
async def get_opportunities(user_id: int):
    optimizer = TaxLossOptimizer(db, user_id, country)
    return optimizer.scan_portfolio()
```

---

**✅ All set! Ready to deploy Production Tax-Loss Harvesting**
