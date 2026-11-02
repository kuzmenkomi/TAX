"""Regression checks for decimal calculations and reconciliation contracts."""
from datetime import datetime, timedelta
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from app.advanced_tax.services.cost_basis_calculator import CostBasisCalculator as Basis, CostBasisLot
from app.advanced_tax.services.cycle_dashboard import CompleteCycleDashboard
from app.advanced_tax.services.liquidity_checker import LiquidityChecker
from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
from app.advanced_tax.services.transaction_matcher import (
    CryptoToFiatAuditTrail, CryptoWithdrawal, MatchingRule, TransactionMatchingEngine,
)
from app.advanced_tax.services.bank_connector import BankTransaction, TransactionType
from app.advanced_tax.utils import ServiceException


@pytest.fixture
def lots():
    return [CostBasisLot("BTC", D("1"), D(price), datetime(2025, month, 1))
            for month, price in [(1, "100"), (2, "200"), (3, "150")]]


@pytest.mark.parametrize("method,expected", [("FIFO", "100"), ("LIFO", "150"), ("AVCO", "150")])
def test_partial_sale_preserves_purchase_lots(lots, method, expected):
    price, sold = Basis.calculate(method, lots, D("0.5"))
    assert price == D(expected)
    assert sum(lot.quantity for lot in sold) == D("0.5")
    assert [lot.quantity for lot in lots] == [D("1")] * 3


def test_specific_lots_and_transaction_conversion(lots):
    price, sold = Basis.specific_id(lots, D("1.5"), [1, 0])
    assert price == D("250") / D("1.5")
    assert [lot.quantity for lot in sold] == [D("1"), D("0.5")]
    converted = Basis.from_transactions([
        {"tx_type": "buy", "asset": "ETH", "amount": "0.25", "price": "2000"},
        {"tx_type": "sell", "asset": "ETH", "amount": "0.1", "price": "2200"},
    ])
    assert len(converted) == 1
    assert converted[0].cost_basis == D("500")
    assert Basis.avco([], D("1")) == (D("0"), [])


@pytest.mark.parametrize("asset,score", [("BTC", 100), ("SOL", 85), ("UNI", 70), ("XYZ", 50), ("PEPE", 5)])
def test_liquidity_heuristics(asset, score):
    actual, description, slippage = LiquidityChecker.assess_liquidity(asset)
    assert actual == score
    assert description
    assert slippage > 0


def test_slippage_scales_with_order_value_and_is_capped():
    amount, pct = LiquidityChecker.estimate_slippage_impact(D("10"), D("100"), D("10000"))
    assert (amount, pct) == (D("10"), D("1"))
    amount, pct = LiquidityChecker.estimate_slippage_impact(D("10000"), D("100"), D("10000"))
    assert (amount, pct) == (D("100000"), D("10"))
    assert LiquidityChecker.suggest_sell_amount("BTC", D("100"), D("100"), D("10000"))[0] == D("2")
    assert LiquidityChecker.suggest_sell_amount("BTC", D("100"), D("100"))[0] == D("10")


def test_harvest_estimate_keeps_decimal_tax_arithmetic():
    optimizer = TaxLossOptimizer(None, 1, "US")
    position = {"last_price": "30000", "quantity": "1", "cost_basis_lots": [
        CostBasisLot("BTC", D("1"), D("40000"), datetime(2024, 1, 1))]}
    result = optimizer._evaluate_asset_for_harvest("BTC", position)
    assert result is not None
    assert result["loss_amount"] == 10000
    assert result["tax_savings"] == 2400
    assert result["estimated_fees"] == 30
    assert result["net_benefit"] == 2355
    assert result["can_harvest"] is True


@pytest.mark.parametrize("position", [{}, {"last_price": 0, "quantity": 1},
    {"last_price": 50000, "quantity": 1, "cost_basis_lots": [
        CostBasisLot("BTC", D("1"), D("40000"), datetime(2024, 1, 1))]}])
def test_harvest_does_not_recommend_missing_data_or_profitable_sales(position):
    assert TaxLossOptimizer(None, 1, "US")._evaluate_asset_for_harvest("BTC", position) is None


@pytest.mark.parametrize("kwargs", [{"quantity": 0}, {"quantity": -1}, {"opportunity_id": 0}])
def test_harvest_rejects_invalid_inputs(kwargs):
    with pytest.raises(ServiceException):
        TaxLossOptimizer(None, 1).validate_inputs(**kwargs)


def test_volatility_uses_observed_prices():
    optimizer = TaxLossOptimizer(None, 1)
    assert optimizer._calculate_volatility("BTC", []) == 0
    assert optimizer._calculate_volatility("BTC", [SimpleNamespace(price=100)] * 2) == 0
    assert optimizer._calculate_volatility("BTC", [SimpleNamespace(price=90), SimpleNamespace(price=110)]) == 10


@pytest.fixture
def withdrawal():
    return CryptoWithdrawal("w1", "binance", "USDC", D("100"), D("100"),
                            datetime(2025, 1, 1, 12), "wallet", "hash")


def deposit(withdrawal, amount="100", hours=1, kind=TransactionType.DEPOSIT, name="d1"):
    return BankTransaction(name, "account", withdrawal.date_time + timedelta(hours=hours),
                           kind, D(amount), "USD", "Exchange payout", "Binance")


def test_matching_selects_closest_deposit_and_serializes_decimal_values(withdrawal):
    engine = TransactionMatchingEngine()
    result = engine.match_withdrawal_to_deposit(withdrawal, [
        deposit(withdrawal, hours=12, name="late"), deposit(withdrawal),
        deposit(withdrawal, kind=TransactionType.FEE, name="fee"),
    ])
    assert result.bank_deposit_id == "d1"
    assert result.confidence == pytest.approx(23 / 24)
    assert result.to_dict()["fiat_amount"] == 100
    assert withdrawal.matched_bank_deposit_id == "d1"
    assert engine.get_total_converted() == {"USD": 100.0}
    assert len(engine.get_matches("USDC")) == 1
    assert engine.get_matches("BTC") == []


@pytest.mark.parametrize("amount,hours,keywords", [("50", 1, []), ("100", 25, []), ("100", 1, ["Kraken"])])
def test_matching_rejects_amount_time_and_counterparty_mismatches(withdrawal, amount, hours, keywords):
    engine = TransactionMatchingEngine()
    result = engine.match_batch([withdrawal], [deposit(withdrawal, amount, hours)], MatchingRule(counterparty_keywords=keywords))
    assert result["matched"] == 0
    assert result["unmatched"] == 1
    assert engine.get_unmatched_withdrawals()[0]["id"] == "w1"
    assert engine.match_batch([], [])["matched"] == 0


def test_conversion_audit_preserves_event_order():
    trail = CryptoToFiatAuditTrail("w1")
    trail.add_event("withdrawal", "Exchange withdrawal", D("100"), "USDC")
    trail.add_event("deposit", "Bank deposit", D("100"), "USD")
    evidence = trail.generate_tax_evidence_pdf()
    assert evidence["transaction_id"] == "w1"
    assert [row["event_type"] for row in evidence["events"]] == ["withdrawal", "deposit"]
    assert evidence["events"][1]["amount"] == 100


def test_cycle_dashboard_empty_and_decimal_summary():
    dashboard = CompleteCycleDashboard()
    empty = dashboard.build_cycle_view([], [], [], [], [])
    assert len(empty) == 7
    assert "COMPLETE CYCLE" in dashboard.render_text_dashboard(empty)
    summary = dashboard._stage7_summary([{"fiat_amount": D("1000")}])
    assert summary["realized_gains_usd"] == 300
    assert summary["estimated_tax_owed_usd"] == 45
