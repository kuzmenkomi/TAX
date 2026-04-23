# 🚨 Critical Issues - Quick Fix Guide

## Issue #1: Hardcoded Placeholder API Key

**File:** [backend/app/ingestion/wallet_importer.py:69](backend/app/ingestion/wallet_importer.py)  
**Severity:** 🔴 CRITICAL  
**Impact:** Wallet syncing will fail or be extremely slow

### Current Code:
```python
class EVMImporter:
    def __init__(self, chain: str = "ethereum", api_key: str = ""):
        self.api_key = api_key or "YourApiKeyToken"  # ❌ PLACEHOLDER!
```

### Fixed Code:
```python
class EVMImporter:
    def __init__(self, chain: str = "ethereum", api_key: str = ""):
        if not api_key and self.chain in {"ethereum", "polygon"}:
            raise ValueError(
                f"API key required for {self.chain} chain. "
                f"Set via environment variable ETHERSCAN_API_KEY or pass via api_key parameter."
            )
        self.api_key = api_key
```

### Additional Fix:
Add to `.env.example`:
```bash
# Blockchain Explorer APIs
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
CRYPTOCOMPARE_API_KEY=your_cryptocompare_key_here
```

---

## Issue #2: ENCRYPTION_KEY Validation Allows Empty String

**File:** [backend/app/core/config.py:72](backend/app/core/config.py)  
**Severity:** 🔴 CRITICAL  
**Impact:** API credential encryption will fail when needed

### Current Code:
```python
if not settings.is_production:
    if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
        settings.JWT_SECRET_KEY = secrets.token_urlsafe(64)
    if not settings.ENCRYPTION_KEY:
        # Fallback for dev if not provided
        settings.ENCRYPTION_KEY = "dev-insecure-but-present-key-for-local-runs-only"
```

### Fixed Code:
```python
# Security check for production
if settings.is_production:
    if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
        raise ValueError(
            "JWT_SECRET_KEY must be set to a strong, unique value in production. "
            "Default or insecure keys are not allowed."
        )
    
    if not settings.ENCRYPTION_KEY:
        raise ValueError(
            "ENCRYPTION_KEY must be set in production via environment variables. "
            "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    
    if settings.ENCRYPTION_KEY == "dev-insecure-but-present-key-for-local-runs-only":
        raise ValueError("Dev encryption key detected in production - this is a critical security issue")

# Auto-generate keys for development only
if not settings.is_production:
    if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
        settings.JWT_SECRET_KEY = secrets.token_urlsafe(64)
    if not settings.ENCRYPTION_KEY:
        settings.ENCRYPTION_KEY = "dev-insecure-but-present-key-for-local-runs-only"
```

---

## Issue #3: Empty Scheduler - No Background Jobs

**File:** [backend/app/scheduler.py](backend/app/scheduler.py)  
**Severity:** 🔴 CRITICAL  
**Impact:** Wallet syncing, exchange syncing, price updates don't work

### Current Code:
```python
# File exists but is completely empty!
```

### Fixed Code:
```python
"""Background job scheduler using APScheduler"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import User, SyncJob
from app.services import sync_service

logger = logging.getLogger(__name__)

scheduler: Optional[BackgroundScheduler] = None


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        return  # Already running
    
    scheduler = BackgroundScheduler()
    
    # Wallet sync every 6 hours
    scheduler.add_job(
        sync_wallet_balances,
        IntervalTrigger(hours=6),
        id="wallet_sync",
        name="Sync wallet balances",
        coalesce=True,
        max_instances=1,
    )
    
    # Exchange sync every 4 hours
    scheduler.add_job(
        sync_exchange_transactions,
        IntervalTrigger(hours=4),
        id="exchange_sync",
        name="Sync exchange transactions",
        coalesce=True,
        max_instances=1,
    )
    
    # Price feed update every 1 hour
    scheduler.add_job(
        update_price_feeds,
        IntervalTrigger(hours=1),
        id="price_update",
        name="Update price feeds",
        coalesce=True,
        max_instances=1,
    )
    
    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is None:
        return
    
    scheduler.shutdown(wait=True)
    scheduler = None
    logger.info("Background scheduler stopped")


def get_sync_status() -> dict:
    """Get status of scheduled sync jobs"""
    if scheduler is None:
        return {"status": "stopped"}
    
    jobs = {}
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs[job.id] = {
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "next_run_in_seconds": (next_run - datetime.now(timezone.utc)).total_seconds() if next_run else None,
        }
    
    return {"status": "running", "jobs": jobs}


def sync_wallet_balances():
    """Sync wallet balances for all users"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"Starting wallet sync for {len(users)} users")
        
        for user in users:
            try:
                sync_service.sync_all_wallets(db, user)
            except Exception as e:
                logger.error(f"Failed to sync wallets for user {user.id}: {e}")
    
    except Exception as e:
        logger.error(f"Wallet sync job failed: {e}")
    finally:
        db.close()


def sync_exchange_transactions():
    """Sync exchange transactions for all users"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"Starting exchange sync for {len(users)} users")
        
        for user in users:
            try:
                sync_service.sync_all_exchanges(db, user)
            except Exception as e:
                logger.error(f"Failed to sync exchanges for user {user.id}: {e}")
    
    except Exception as e:
        logger.error(f"Exchange sync job failed: {e}")
    finally:
        db.close()


def update_price_feeds():
    """Update price feeds for all assets"""
    try:
        logger.info("Starting price feed update")
        sync_service.update_all_prices()
    except Exception as e:
        logger.error(f"Price feed update failed: {e}")
```

### Update app/api/server.py lifespan:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    from app.scheduler import start_scheduler
    
    if not get_settings().is_production:
        Base.metadata.create_all(bind=engine)
        initialize_database()
    
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start background scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    from app.scheduler import stop_scheduler
    stop_scheduler()
```

---

## Issue #4: Hardcoded Database Password in docker-compose.yml

**File:** [docker-compose.yml:9](docker-compose.yml)  
**Severity:** 🔴 CRITICAL  
**Impact:** Security vulnerability if .env file not created

### Current Code:
```yaml
postgres:
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-taxuser}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-taxpass123}  # ❌ DEFAULT PASSWORD!
```

### Fixed Code:
```yaml
postgres:
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB:-tax_app_db}
```

### Create .env file with strong values:
```bash
# Database
POSTGRES_USER=tax_user_prod
POSTGRES_PASSWORD=$(openssl rand -base64 32)  # Generate strong password
POSTGRES_DB=tax_app_db

# Add validation to docker-compose startup
# (fail if .env not found)
```

### Update docker-compose.yml:
```yaml
version: '3.8'

# Add this check at the top
x-variables:
  env_file: &env_file
    - .env

services:
  postgres:
    image: postgres:16-alpine
    container_name: tax-postgres
    env_file: *env_file  # Uses .env file
    # Rest of config...
```

---

## Issue #5: Frontend API URL Hardcoded to localhost

**File:** [frontend/.env](frontend/.env) and [frontend/src/api/client.ts](frontend/src/api/client.ts)  
**Severity:** 🔴 CRITICAL  
**Impact:** Frontend won't connect to backend in production

### Current Code:
```typescript
// client.ts
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '') + '/api/v1';
```

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000
```

### Fixed Code:

Option A (Simplest - Relative URLs):
```typescript
// client.ts
const API_PREFIX = '/api/v1';

export function apiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${API_PREFIX}${path.startsWith('/') ? path : `/${path}`}`;
}
```

Option B (Environment Variable - More Control):
```typescript
// client.ts
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '') + '/api/v1';

// Validate in development
if (import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL) {
  console.warn('VITE_API_BASE_URL not set, using /api');
}

// Fail fast in production if not set
if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  throw new Error('VITE_API_BASE_URL environment variable required in production');
}
```

Create .env files:
```bash
# .env (development)
VITE_API_BASE_URL=http://localhost:8000

# .env.production (production build)
VITE_API_BASE_URL=/api

# .env.staging (staging)
VITE_API_BASE_URL=https://api-staging.declairo.com

# .env.example (for repo)
# Frontend API Base URL
# Use relative path /api for same-domain deployments
# Use absolute URL for separate domain deployments
VITE_API_BASE_URL=/api
```

### Update vite.config.ts:
```typescript
import { defineConfig } from 'vite';

export default defineConfig({
  // ... existing config
  
  define: {
    // Ensure env vars are available
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL || '/api'),
  },
});
```

---

## Summary Table

| Issue | Fix Time | Priority |
|-------|----------|----------|
| Remove hardcoded API key | 1-2 hrs | 🔴 CRITICAL |
| Fix ENCRYPTION_KEY validation | 1 hr | 🔴 CRITICAL |
| Implement scheduler | 3-4 hrs | 🔴 CRITICAL |
| Remove hardcoded DB password | 30 min | 🔴 CRITICAL |
| Fix frontend API URL | 1-2 hrs | 🔴 CRITICAL |
| **Total** | **7-10 hrs** | - |

---

## Testing After Fixes

```bash
# Test 1: Environment variables fail gracefully
unset ENCRYPTION_KEY
pytest tests/  # Should fail with clear error

# Test 2: Scheduler starts correctly
python -c "from app.scheduler import start_scheduler; start_scheduler()"

# Test 3: Wallet importer fails without API key
python -c "from app.ingestion.wallet_importer import EVMImporter; EVMImporter('ethereum')"  # Should raise

# Test 4: Frontend builds with env var
VITE_API_BASE_URL=https://api.example.com npm run build
```

---

**Estimated Time to Production:** 1-2 weeks with these fixes + security hardening
