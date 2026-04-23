"""
Tests for Banking API endpoints
Unit and integration tests for Open Banking integration
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.server import create_app
from app.core.db import Base, get_db
from app.models import (
    BankAccount,
    BankTransaction,
    TransactionMatch,
    CryptoWithdrawal,
    BankType,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    async with TestingSessionLocal() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client"""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_bank_account(test_db):
    """Create sample bank account"""
    account = BankAccount(
        id="bank_acc_1",
        user_id="test_user",
        bank_type=BankType.NUBANK.value,
        account_number="12345678",
        account_name="My Nubank Account",
        currency="BRL",
        balance=Decimal("50000"),
        sync_status="synced",
        connected_at=datetime.utcnow(),
    )
    test_db.add(account)
    await test_db.commit()
    await test_db.refresh(account)
    return account


@pytest.fixture
async def sample_bank_transaction(test_db, sample_bank_account):
    """Create sample bank transaction"""
    txn = BankTransaction(
        id="bank_txn_1",
        account_id=sample_bank_account.id,
        date=datetime.utcnow(),
        type="deposit",
        amount=Decimal("1000"),
        currency="BRL",
        description="Deposit from exchange",
        counterparty="Binance",
        balance_after=Decimal("51000"),
    )
    test_db.add(txn)
    await test_db.commit()
    await test_db.refresh(txn)
    return txn


@pytest.fixture
async def sample_crypto_withdrawal(test_db):
    """Create sample crypto withdrawal"""
    withdrawal = CryptoWithdrawal(
        id="crypto_wd_1",
        user_id="test_user",
        exchange="binance",
        asset="BTC",
        amount=Decimal("0.05"),
        amount_in_usd=Decimal("1000"),
        destination_address="1A1z7agoat7d9pZtEXzXHJkk3zPT2UhAML",
        tx_hash="0x123456789abcdef",
        status="completed",
        date_time=datetime.utcnow(),
    )
    test_db.add(withdrawal)
    await test_db.commit()
    await test_db.refresh(withdrawal)
    return withdrawal


# ============================================================================
# BANK ACCOUNT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_connect_bank_account(client, test_db):
    """Test connecting new bank account"""
    payload = {
        "bank_type": "nubank",
        "account_number": "87654321",
        "account_name": "Test Account",
        "currency": "BRL",
        "api_key": "test_key",
        "api_secret": "test_secret",
    }
    response = await client.post("/api/v1/banking/accounts/connect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["bank_type"] == "nubank"
    assert data["account_name"] == "Test Account"


@pytest.mark.asyncio
async def test_connect_invalid_bank(client, test_db):
    """Test connecting with invalid bank type"""
    payload = {
        "bank_type": "invalid_bank",
        "account_number": "87654321",
        "account_name": "Test",
        "currency": "BRL",
    }
    response = await client.post("/api/v1/banking/accounts/connect", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_bank_accounts_empty(client, test_db):
    """Test listing accounts when none connected"""
    response = await client.get("/api/v1/banking/accounts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_bank_accounts(client, test_db, sample_bank_account):
    """Test listing connected bank accounts"""
    response = await client.get("/api/v1/banking/accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["bank_type"] == "nubank"


@pytest.mark.asyncio
async def test_get_bank_account(client, test_db, sample_bank_account):
    """Test getting specific bank account"""
    response = await client.get(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_bank_account.id
    assert data["account_number"] == "12345678"


@pytest.mark.asyncio
async def test_get_nonexistent_account(client, test_db):
    """Test getting non-existent account"""
    response = await client.get("/api/v1/banking/accounts/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_bank_transactions(client, test_db, sample_bank_account):
    """Test syncing bank transactions"""
    payload = {
        "days_back": 30,
        "force_full_sync": False,
    }
    response = await client.post(
        f"/api/v1/banking/accounts/{sample_bank_account.id}/sync",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == sample_bank_account.id
    assert data["status"] in ["success", "no_new_transactions"]


@pytest.mark.asyncio
async def test_disconnect_account(client, test_db, sample_bank_account):
    """Test disconnecting bank account"""
    response = await client.delete(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disconnected"
    
    # Verify deletion
    response = await client.get(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 404


# ============================================================================
# BANK TRANSACTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_transactions_empty(client, test_db):
    """Test listing transactions when none exist"""
    response = await client.get("/api/v1/banking/transactions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_transactions(client, test_db, sample_bank_transaction):
    """Test listing bank transactions"""
    response = await client.get("/api/v1/banking/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "deposit"


@pytest.mark.asyncio
async def test_list_transactions_filter_type(client, test_db, sample_bank_transaction):
    """Test filtering transactions by type"""
    response = await client.get("/api/v1/banking/transactions?type=deposit")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "deposit"


@pytest.mark.asyncio
async def test_list_transactions_filter_amount(client, test_db, sample_bank_transaction):
    """Test filtering transactions by amount"""
    response = await client.get("/api/v1/banking/transactions?min_amount=500&max_amount=1500")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


# ============================================================================
# TRANSACTION MATCHING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_transaction_match(client, test_db, sample_bank_transaction):
    """Test creating transaction match"""
    payload = {
        "crypto_withdrawal_id": "crypto_wd_1",
        "bank_deposit_id": sample_bank_transaction.id,
        "crypto_amount": "0.05",
        "crypto_currency": "BTC",
        "fiat_amount": "1000",
        "fiat_currency": "BRL",
        "exchange_rate": "20000",
        "fees_paid": "10",
    }
    response = await client.post("/api/v1/banking/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crypto_currency"] == "BTC"
    assert data["match_status"] == "matched"
    assert data["confidence"] == 1.0


@pytest.mark.asyncio
async def test_auto_match_transactions(client, test_db, sample_bank_transaction, sample_crypto_withdrawal):
    """Test automatic transaction matching"""
    payload = {
        "tolerance_percent": 2.0,
        "time_window_hours": 24,
    }
    response = await client.post("/api/v1/banking/match-auto", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should find matches based on algorithms
    assert "matches_found" in data


@pytest.mark.asyncio
async def test_list_matches_empty(client, test_db):
    """Test listing matches when none exist"""
    response = await client.get("/api/v1/banking/matches")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_matches_with_data(client, test_db, sample_bank_transaction):
    """Test listing transaction matches"""
    # Create a match
    match = TransactionMatch(
        id="match_1",
        crypto_withdrawal_id="crypto_wd_1",
        bank_deposit_id=sample_bank_transaction.id,
        crypto_amount=Decimal("0.05"),
        crypto_currency="BTC",
        fiat_amount=Decimal("1000"),
        fiat_currency="BRL",
        exchange_rate=Decimal("20000"),
        fees_paid=Decimal("10"),
        crypto_date=datetime.utcnow() - timedelta(hours=2),
        fiat_date=datetime.utcnow(),
        time_delta_hours=2.0,
        confidence=0.95,
    )
    test_db.add(match)
    await test_db.commit()
    
    response = await client.get("/api/v1/banking/matches")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["confidence"] == 0.95


# ============================================================================
# CYCLE DASHBOARD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_cycle_dashboard_empty(client, test_db):
    """Test cycle dashboard with no data"""
    response = await client.get("/api/v1/banking/cycle-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    assert data["matched_cycles"] == 0


@pytest.mark.asyncio
async def test_get_cycle_dashboard_with_data(client, test_db, sample_bank_account):
    """Test cycle dashboard with accounts"""
    response = await client.get("/api/v1/banking/cycle-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_positions"] >= 1


# ============================================================================
# METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_banking_metrics_empty(client, test_db):
    """Test banking metrics with no data"""
    response = await client.get("/api/v1/banking/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["connected_banks"] == 0
    assert data["total_transactions"] == 0


@pytest.mark.asyncio
async def test_get_banking_metrics_with_data(client, test_db, sample_bank_account, sample_bank_transaction):
    """Test banking metrics with data"""
    response = await client.get("/api/v1/banking/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["connected_banks"] >= 1
    assert data["total_transactions"] >= 1


# ============================================================================
# HEALTH CHECK
# ============================================================================

@pytest.mark.asyncio
async def test_banking_health_check(client):
    """Test banking health check endpoint"""
    response = await client.get("/api/v1/banking/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "banking"
