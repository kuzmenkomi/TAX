"""
Tests for Banking API endpoints.

Uses synchronous TestClient + conftest dependency overrides (same pattern as
test_tlh_endpoints). Async httpx + wrong get_db overrides caused 401/404 on all routes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.main import app
from sqlalchemy import delete, select

from app.models import (
    BankAccount,
    BankTransaction,
    BankType,
    CryptoWithdrawal,
    TransactionMatch,
)


def _session_user_id() -> str:
    override_fn = app.dependency_overrides.get(get_current_user)
    assert override_fn is not None
    user = override_fn()
    return str(user.id)


def _purge_banking_for_session_user(db) -> None:
    """Remove banking rows for the test user (API commits bypass nested txn rollback)."""
    uid = _session_user_id()
    acc_ids = list(db.scalars(select(BankAccount.id).where(BankAccount.user_id == uid)).all())
    if acc_ids:
        tx_ids = list(db.scalars(select(BankTransaction.id).where(BankTransaction.account_id.in_(acc_ids))).all())
        if tx_ids:
            db.execute(delete(TransactionMatch).where(TransactionMatch.bank_deposit_id.in_(tx_ids)))
        db.execute(delete(BankTransaction).where(BankTransaction.account_id.in_(acc_ids)))
    db.execute(delete(BankAccount).where(BankAccount.user_id == uid))
    db.execute(delete(CryptoWithdrawal).where(CryptoWithdrawal.user_id == uid))
    db.commit()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_bank_account(db):
    user_id = _session_user_id()
    account = BankAccount(
        id=f"bank_acc_{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        bank_type=BankType.NUBANK.value,
        account_number="12345678",
        account_name="My Nubank Account",
        currency="BRL",
        balance=Decimal("50000"),
        sync_status="synced",
        connected_at=datetime.utcnow(),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def sample_bank_transaction(db, sample_bank_account):
    tid = f"bank_txn_{uuid.uuid4().hex[:8]}"
    txn = BankTransaction(
        id=tid,
        account_id=sample_bank_account.id,
        date=datetime.utcnow(),
        type="deposit",
        amount=Decimal("1000"),
        currency="BRL",
        description="Deposit from exchange",
        counterparty="Binance",
        balance_after=Decimal("51000"),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@pytest.fixture
def sample_crypto_withdrawal(db):
    user_id = _session_user_id()
    wid = f"crypto_wd_{uuid.uuid4().hex[:8]}"
    withdrawal = CryptoWithdrawal(
        id=wid,
        user_id=user_id,
        exchange="binance",
        asset="BTC",
        amount=Decimal("0.05"),
        amount_in_usd=Decimal("1000"),
        destination_address="1A1z7agoat7d9pZtEXzXHJkk3zPT2UhAML",
        tx_hash="0x123456789abcdef",
        status="completed",
        date_time=datetime.utcnow(),
    )
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


# ============================================================================
# BANK ACCOUNT TESTS
# ============================================================================


def test_connect_bank_account(client):
    payload = {
        "bank_type": "nubank",
        "account_number": "87654321",
        "account_name": "Test Account",
        "currency": "BRL",
        "api_key": "test_key",
        "api_secret": "test_secret",
    }
    response = client.post("/api/v1/banking/accounts/connect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["bank_type"] == "nubank"
    assert data["account_name"] == "Test Account"


def test_connect_invalid_bank(client):
    payload = {
        "bank_type": "invalid_bank",
        "account_number": "87654321",
        "account_name": "Test",
        "currency": "BRL",
    }
    response = client.post("/api/v1/banking/accounts/connect", json=payload)
    assert response.status_code == 400


def test_list_bank_accounts_empty(client, db):
    _purge_banking_for_session_user(db)
    response = client.get("/api/v1/banking/accounts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_bank_accounts(client, sample_bank_account):
    response = client.get("/api/v1/banking/accounts")
    assert response.status_code == 200
    data = response.json()
    mine = [x for x in data if x["id"] == sample_bank_account.id]
    assert len(mine) == 1
    assert mine[0]["bank_type"] == "nubank"


def test_get_bank_account(client, sample_bank_account):
    response = client.get(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_bank_account.id
    assert data["account_number"] == "12345678"


def test_get_nonexistent_account(client):
    response = client.get("/api/v1/banking/accounts/nonexistent")
    assert response.status_code == 404


def test_sync_bank_transactions(client, sample_bank_account):
    payload = {
        "days_back": 30,
        "force_full_sync": False,
    }
    response = client.post(
        f"/api/v1/banking/accounts/{sample_bank_account.id}/sync",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == sample_bank_account.id
    assert data["status"] in ["success", "no_new_transactions"]


def test_disconnect_account(client, sample_bank_account):
    response = client.delete(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disconnected"

    response = client.get(f"/api/v1/banking/accounts/{sample_bank_account.id}")
    assert response.status_code == 404


# ============================================================================
# BANK TRANSACTION TESTS
# ============================================================================


def test_list_transactions_empty(client, db):
    _purge_banking_for_session_user(db)
    response = client.get("/api/v1/banking/transactions")
    assert response.status_code == 200
    assert response.json() == []


def test_list_transactions(client, sample_bank_transaction):
    response = client.get("/api/v1/banking/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "deposit"


def test_list_transactions_filter_type(client, sample_bank_transaction):
    response = client.get("/api/v1/banking/transactions?type=deposit")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "deposit"


def test_list_transactions_filter_amount(client, sample_bank_transaction):
    response = client.get("/api/v1/banking/transactions?min_amount=500&max_amount=1500")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


# ============================================================================
# TRANSACTION MATCHING TESTS
# ============================================================================


def test_create_transaction_match(client, sample_bank_transaction, sample_crypto_withdrawal):
    payload = {
        "crypto_withdrawal_id": sample_crypto_withdrawal.id,
        "bank_deposit_id": sample_bank_transaction.id,
        "crypto_amount": "0.05",
        "crypto_currency": "BTC",
        "fiat_amount": "1000",
        "fiat_currency": "BRL",
        "exchange_rate": "20000",
        "fees_paid": "10",
    }
    response = client.post("/api/v1/banking/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crypto_currency"] == "BTC"
    assert data["match_status"] == "matched"
    assert data["confidence"] == 1.0


def test_auto_match_transactions(client, sample_bank_transaction, sample_crypto_withdrawal):
    payload = {
        "tolerance_percent": 2.0,
        "time_window_hours": 24,
    }
    response = client.post("/api/v1/banking/match-auto", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "matches_found" in data


def test_list_matches_empty(client, db):
    _purge_banking_for_session_user(db)
    response = client.get("/api/v1/banking/matches")
    assert response.status_code == 200
    assert response.json() == []


def test_list_matches_with_data(client, db, sample_bank_transaction, sample_crypto_withdrawal):
    match = TransactionMatch(
        id=f"match_{uuid.uuid4().hex[:8]}",
        crypto_withdrawal_id=sample_crypto_withdrawal.id,
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
    db.add(match)
    db.commit()

    response = client.get("/api/v1/banking/matches")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["confidence"] == 0.95


# ============================================================================
# CYCLE DASHBOARD TESTS
# ============================================================================


def test_get_cycle_dashboard_empty(client, db):
    _purge_banking_for_session_user(db)
    response = client.get("/api/v1/banking/cycle-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == _session_user_id()
    assert data["matched_cycles"] == 0


def test_get_cycle_dashboard_with_data(client, sample_bank_account):
    response = client.get("/api/v1/banking/cycle-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_positions"] >= 1


# ============================================================================
# METRICS TESTS
# ============================================================================


def test_get_banking_metrics_empty(client, db):
    _purge_banking_for_session_user(db)
    response = client.get("/api/v1/banking/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["connected_banks"] == 0
    assert data["total_transactions"] == 0


def test_get_banking_metrics_with_data(client, sample_bank_account, sample_bank_transaction):
    response = client.get("/api/v1/banking/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["connected_banks"] >= 1
    assert data["total_transactions"] >= 1


# ============================================================================
# HEALTH CHECK
# ============================================================================


def test_banking_health_check(client):
    response = client.get("/api/v1/banking/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "banking"
