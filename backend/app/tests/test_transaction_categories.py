from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Transaction, User
from app.services.transaction_categories import classify_transaction_category


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_classify_transaction_category_known_types():
    assert classify_transaction_category("BUY") == "TRADE"
    assert classify_transaction_category("SWAP") == "TRADE"
    assert classify_transaction_category("TRANSFER") == "TRANSFER"
    assert classify_transaction_category("TOKEN_TRANSFER") == "TRANSFER"
    assert classify_transaction_category("STAKING_REWARD") == "INCOME"
    assert classify_transaction_category("LENDING_INTEREST") == "INCOME"


def test_classify_transaction_category_heuristics_and_custom_tags():
    assert classify_transaction_category("governance_reward_claim") == "INCOME"
    assert classify_transaction_category("cross_chain_bridge_out") == "TRANSFER"
    assert classify_transaction_category("perp_trade_settlement") == "TRADE"
    assert classify_transaction_category("BUY", custom_tag="personal") == "TRANSFER"
    assert classify_transaction_category("TRANSFER", custom_tag="salary") == "INCOME"
    assert classify_transaction_category("mystery_event") == "OTHER"


def test_wallet_transactions_endpoint_returns_category(client: TestClient, db):
    user = db.query(User).first()
    assert user is not None

    now = datetime.now(timezone.utc)
    db.add_all([
        Transaction(
            user_id=user.id,
            timestamp=now,
            asset="ETH",
            tx_type="STAKING_REWARD",
            amount=Decimal("0.5"),
            fee=Decimal("0"),
            price=Decimal("3000"),
            total_value=Decimal("1500"),
            from_wallet="wallet-1",
            to_wallet="wallet-1",
            external_id="tx-income-1",
        ),
        Transaction(
            user_id=user.id,
            timestamp=now,
            asset="BTC",
            tx_type="BUY",
            amount=Decimal("0.1"),
            fee=Decimal("0"),
            price=Decimal("65000"),
            total_value=Decimal("6500"),
            from_wallet="binance",
            to_wallet="binance",
            external_id="tx-trade-1",
        ),
        Transaction(
            user_id=user.id,
            timestamp=now,
            asset="USDC",
            tx_type="TOKEN_TRANSFER",
            amount=Decimal("250"),
            fee=Decimal("2"),
            price=Decimal("1"),
            total_value=Decimal("250"),
            from_wallet="wallet-2",
            to_wallet="wallet-3",
            external_id="tx-transfer-1",
        ),
    ])
    db.commit()

    response = client.get("/api/v1/br/wallet/transactions?limit=10")
    assert response.status_code == 200

    payload = response.json()
    category_by_type = {item["type"]: item["category"] for item in payload}

    assert category_by_type["STAKING_REWARD"] == "INCOME"
    assert category_by_type["BUY"] == "TRADE"
    assert category_by_type["TOKEN_TRANSFER"] == "TRANSFER"


def test_wallet_transactions_endpoint_filters_by_category(client: TestClient, db):
    user = db.query(User).first()
    assert user is not None

    now = datetime.now(timezone.utc)
    db.add_all([
        Transaction(
            user_id=user.id,
            timestamp=now,
            asset="ETH",
            tx_type="STAKING_REWARD",
            amount=Decimal("1"),
            fee=Decimal("0"),
            price=Decimal("2500"),
            total_value=Decimal("2500"),
            from_wallet="wallet-1",
            to_wallet="wallet-1",
            external_id="tx-filter-income",
        ),
        Transaction(
            user_id=user.id,
            timestamp=now,
            asset="BTC",
            tx_type="BUY",
            amount=Decimal("0.2"),
            fee=Decimal("0"),
            price=Decimal("60000"),
            total_value=Decimal("12000"),
            from_wallet="cex-1",
            to_wallet="cex-1",
            external_id="tx-filter-trade",
        ),
    ])
    db.commit()

    response = client.get("/api/v1/br/wallet/transactions?category=INCOME&limit=50")
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) >= 1
    assert all(item["category"] == "INCOME" for item in payload)
    assert all(item["type"] != "BUY" for item in payload)
