"""Service-level workflows against a fresh database and mocked network boundaries."""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db import Base
from app.models import User, Transaction, Subscription, AnalysisRun, RefreshToken
from app.services import portfolio_service as portfolios, exchange_service as exchanges
from app.services import wallet_service as wallets, billing_service as billing, auth_service as auth
from app.services.financial_data_service import FinancialDataService as Financial


@pytest.fixture
def store():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(email="owner@example.com", hashed_password="unused", jurisdiction_code="US")
        other = User(email="other@example.com", hashed_password="unused", jurisdiction_code="BR")
        db.add_all([user, other])
        db.commit()
        yield db, user, other
    engine.dispose()


def add_trade(db, user, year=2024, kind="BUY", amount=1, price=100, **extra):
    row = Transaction(user_id=user.id, timestamp=datetime(year, 6, 1), asset="BTC", tx_type=kind,
                      amount=amount, price=price, total_value=amount * price, **extra)
    db.add(row)
    db.commit()
    return row


def test_portfolio_onboarding_normalizes_and_persists_country(store):
    db, user, other = store
    first = portfolios.get_or_create_portfolio(db, user)
    assert first.base_currency == "USD"
    assert portfolios.get_or_create_portfolio(db, user).id == first.id
    updated = portfolios.complete_onboarding(db, user, " br ", " PERSONAL ", " SMALL ")
    assert updated.country_code == user.jurisdiction_code == "BR"
    assert updated.tax_structure == "personal"
    assert updated.is_onboarded and updated.country_locked
    assert portfolios.get_or_create_portfolio(db, other).id != first.id


def test_portfolio_snapshot_filters_future_trades_and_other_users(store):
    db, user, other = store
    add_trade(db, user, price=100)
    add_trade(db, user, year=2025, price=500)
    add_trade(db, other, price=999)
    result = portfolios.get_dashboard(db, user, tax_year=2024)
    assert result["prices_as_of"] == "year_end"
    assert result["accounting_method"] == "FIFO"
    assert result["total_cost_basis_usd"] == 100
    assert result["total_current_value_usd"] == 100
    assert len(result["positions"]) == 1


def test_portfolio_latest_run_method_and_bad_json_fallback(store):
    db, user, _ = store
    assert portfolios.get_dashboard(db, user)["positions"] == []
    row = AnalysisRun(user_id=user.id, csv_rel_path="unused.csv", summary_json=json.dumps({"accounting_method": "lifo"}))
    db.add(row)
    db.commit()
    assert portfolios._resolve_accounting_method(db, user) == "LIFO"
    row.summary_json = "invalid-json"
    db.commit()
    assert portfolios._resolve_accounting_method(db, user) == "FIFO"


def test_live_prices_fall_back_to_last_observed_price(monkeypatch):
    frame = pd.DataFrame([{"timestamp": datetime(2025, 1, 1), "asset": "BTC", "type": "BUY", "amount": 1, "price": 100, "fee": 0}])
    monkeypatch.setattr(portfolios.PriceService, "get_current_prices_for_assets", Mock(side_effect=RuntimeError("offline")))
    assert portfolios._live_prices_for_positions(frame) == {"btc": 100.0}
    stable = frame.assign(asset="USDC", price=1)
    assert portfolios._live_prices_for_positions(stable) == {"usdc": 1.0}
    assert portfolios._latest_known_prices(pd.DataFrame()) == {}


def test_exchange_connection_encrypts_secrets_and_is_user_scoped(store, monkeypatch):
    db, user, other = store
    from app.integrations import exchange_ccxt_adapter
    adapter = SimpleNamespace(get_balance=Mock(return_value={}))
    monkeypatch.setattr(exchange_ccxt_adapter, "get_exchange_adapter", Mock(return_value=adapter))
    conn = exchanges.connect_exchange(db, user, "binance", "demo-key", "demo-secret")
    stored = db.execute(text("SELECT api_key, api_secret FROM exchange_connections WHERE id = :id"), {"id": conn.id}).one()
    assert stored.api_key != "demo-key"
    assert stored.api_secret != "demo-secret"
    assert conn.api_key == "demo-key"  # ORM decrypts only after reading storage.
    assert conn.status == "connected"
    assert len(exchanges.get_user_exchanges(db, user)) == 1
    assert exchanges.get_user_exchanges(db, other) == []
    with pytest.raises(HTTPException) as denied:
        exchanges.disconnect_exchange(db, other, conn.id)
    assert denied.value.status_code == 404
    monkeypatch.setattr(exchange_ccxt_adapter, "fetch_exchange_transactions", Mock(return_value=pd.DataFrame()))
    assert exchanges.sync_exchange(db, user, conn.id)["transactions_found"] == 0
    monkeypatch.setattr(exchange_ccxt_adapter, "fetch_exchange_transactions", Mock(side_effect=RuntimeError("offline")))
    with pytest.raises(HTTPException):
        exchanges.sync_exchange(db, user, conn.id)
    assert conn.status == "error"
    exchanges.disconnect_exchange(db, user, conn.id)
    assert exchanges.get_user_exchanges(db, user) == []


def test_exchange_authentication_failure_does_not_save_credentials(store, monkeypatch):
    db, user, _ = store
    from app.integrations import exchange_ccxt_adapter
    monkeypatch.setattr(exchange_ccxt_adapter, "get_exchange_adapter", Mock(side_effect=ValueError("invalid credentials")))
    with pytest.raises(HTTPException) as error:
        exchanges.connect_exchange(db, user, "binance", "key", "secret")
    assert error.value.status_code == 400
    assert exchanges.get_user_exchanges(db, user) == []


def test_wallet_deduplication_import_empty_and_delete_permissions(store, monkeypatch):
    db, user, other = store
    wallet = wallets.create_wallet(db, user, " Ethereum ", " 0xabc ", " Main ")
    assert wallet.label == "Main"
    assert wallets.create_wallet(db, user, "ethereum", "0xabc").id == wallet.id
    monkeypatch.setattr(wallets, "fetch_wallet_transactions", Mock(return_value=pd.DataFrame()))
    assert wallets.import_blockchain_wallet(db, user, "ethereum", "0xabc")["transactions_count"] == 0
    assert wallets.list_connections(db, user)["wallets"][0]["address"] == "0xabc"
    with pytest.raises(HTTPException) as denied:
        wallets.delete_wallet(db, other, wallet.id)
    assert denied.value.status_code == 404
    wallets.delete_wallet(db, user, wallet.id)
    assert wallets.list_connections(db, user)["wallets"] == []


def test_wallet_import_failure_is_recorded(store, monkeypatch):
    db, user, _ = store
    monkeypatch.setattr(wallets, "fetch_wallet_transactions", Mock(side_effect=RuntimeError("offline")))
    with pytest.raises(HTTPException) as error:
        wallets.import_blockchain_wallet(db, user, "ethereum", "0xfailure")
    assert error.value.status_code == 500
    from app.models import ImportJob
    assert db.query(ImportJob).one().status == "failed"
    with pytest.raises(HTTPException):
        wallets.import_blockchain_wallet(db, user, "unknown", "address")


@pytest.mark.parametrize("feature", ["pdf", "ai"])
def test_paid_features_require_active_subscription(store, feature):
    db, user, _ = store
    with pytest.raises(HTTPException) as error:
        billing.check_limit(db, user.id, feature)
    assert error.value.status_code == 403
    sub = Subscription(user_id=user.id, plan="pro", status="active")
    db.add(sub)
    db.commit()
    assert billing.check_limit(db, user.id, feature) is None
    sub.status = "canceled"
    db.commit()
    assert billing.get_user_plan(db, user.id) == "free"


def test_verification_and_password_reset_are_one_time_tokens(store):
    db, user, _ = store
    user.verification_token = "verify-once"
    db.commit()
    assert auth.verify_email(db, "verify-once").is_email_verified
    with pytest.raises(HTTPException):
        auth.verify_email(db, "verify-once")
    assert auth.request_password_reset(db, "unknown@example.com") is None
    token = auth.request_password_reset(db, user.email)
    assert token
    auth.confirm_password_reset(db, token, "NewPassword123!")
    assert user.password_reset_token is None
    assert auth.login_user(db, user.email, "NewPassword123!")
    with pytest.raises(HTTPException):
        auth.confirm_password_reset(db, token, "AnotherPassword123!")


def test_refresh_rotation_and_reuse_revoke_other_sessions(store):
    db, user, _ = store
    from app.auth import create_refresh_token
    token = create_refresh_token({"sub": user.email, "jti": "one"})
    auth.save_refresh_token(db, user.id, token, datetime.now(timezone.utc) + timedelta(days=1))
    assert auth.verify_refresh_token(db, token).id == user.id
    another = create_refresh_token({"sub": user.email, "jti": "two"})
    auth.save_refresh_token(db, user.id, another, datetime.now(timezone.utc) + timedelta(days=1))
    with pytest.raises(HTTPException) as error:
        auth.verify_refresh_token(db, token)
    assert error.value.status_code == 401
    assert all(row.revoked for row in db.query(RefreshToken).all())


def test_financial_data_parses_rates_and_falls_back_on_outage(monkeypatch):
    import app.services.financial_data_service as module
    response = Mock()
    response.json.return_value = {"rates": {"EUR": "0.91"}, "blue": {"value_sell": 1200}, "bitcoin": {"usd": 50000}}
    request = Mock(return_value=response)
    monkeypatch.setattr(module.requests, "get", request)
    assert Financial.get_exchange_rate("USD", "EUR", datetime(2025, 1, 2)) == Decimal("0.91")
    assert "2025-01-02" in request.call_args.args[0]
    assert Financial.get_parallel_rate("USD", "ARS") == Decimal("1200")
    assert Financial.get_crypto_price("BTC") == Decimal("50000")
    request.side_effect = RuntimeError("offline")
    assert Financial.get_exchange_rate("USD", "BRL") == Decimal("5")
    assert Financial.get_crypto_price("BTC") == 0
    assert Financial.get_exchange_rate("USD", "USD") == 1
