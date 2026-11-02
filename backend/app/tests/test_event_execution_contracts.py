"""Threshold/cooldown behavior and exchange execution failure isolation."""
from datetime import datetime, timedelta
from decimal import Decimal as D
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.advanced_tax.services.tlh_event_listener import (
    TLHEventListener, TLHEventReactor, PriceEvent, PriceEventType, PriceFeedListener,
)
from app.advanced_tax.services.tlh_executor import TLHExecutor, ImmediateExecutionStrategy, ScheduledExecutionStrategy
from app.advanced_tax.services.cycle_dashboard import CompleteCycleDashboard


def test_threshold_cooldown_and_subscriber_failure_isolation():
    listener = TLHEventListener()
    good = Mock()
    bad = Mock(side_effect=RuntimeError("subscriber offline"))
    listener.subscribe(bad)
    listener.subscribe(good)
    listener.register_asset("BTC", drop_threshold_pct=5)
    feed = PriceFeedListener(listener)
    assert feed.update_price("BTC", D("100")) is None
    assert feed.update_price("BTC", D("96")) is None
    event = feed.update_price("BTC", D("90"))
    assert event.event_type == PriceEventType.PRICE_DROP
    good.assert_called_once_with(event)
    assert feed.update_price("BTC", D("80")) is None  # Five-minute cooldown.
    listener.thresholds["BTC"].last_event_time = datetime.now() - timedelta(minutes=6)
    assert feed.update_price("BTC", D("80")) is not None
    assert len(listener.get_event_history("BTC")) == 2
    listener.unsubscribe(bad)
    listener.unregister_asset("BTC")
    assert feed.update_price("BTC", D("70")) is None


def test_realized_loss_threshold_and_bounded_history():
    listener = TLHEventListener()
    listener.max_history_size = 2
    listener.register_asset("ETH")
    assert listener.on_loss_realized("ETH", D("250"), D("200")) is None
    assert listener.on_loss_realized("ETH", D("150"), D("200")) is None
    for _ in range(3):
        assert listener.on_loss_realized("ETH", D("100"), D("200")) is not None
    assert len(listener.get_event_history()) == 2
    assert listener.get_event_history("BTC") == []
    assert listener.on_loss_realized("UNKNOWN", D("100"), D("200")) is None


def test_reactor_dispatches_only_registered_handlers():
    reactor = TLHEventReactor(None)
    event = PriceEvent(PriceEventType.PRICE_DROP, "BTC", D("100"), D("90"), datetime.now())
    handler = Mock()
    reactor.register_reaction(PriceEventType.PRICE_DROP, handler)
    reactor.on_event(event)
    handler.assert_called_once_with(event)
    assert event.to_dict()["price_change_pct"] == -10
    reactor.set_default_reactions()
    reactor.on_event(event)
    reactor.on_event(PriceEvent(PriceEventType.LOSS_REALIZED, "BTC", D("200"), D("100"), datetime.now(), {"loss_amount": 100}))


def test_execution_passes_order_fields_and_reports_exchange_failure():
    exchange = SimpleNamespace(sell_market=Mock(return_value={"id": "order-1", "filled": 2, "average": 100, "fee": {"cost": 0.2}}),
        fetch_order=Mock(return_value={"id": "order-1", "status": "closed", "filled": 2, "remaining": 0, "average": 100}))
    executor = TLHExecutor(exchange)
    result = ImmediateExecutionStrategy(executor).execute("BTC", D("2"), D("100"))
    assert result.success and result.to_dict()["fees_paid"] == 0.2
    exchange.sell_market.assert_called_once_with(symbol="BTC/USD", quantity=2.0)
    assert executor.verify_execution("order-1")["remaining"] == 0
    exchange.sell_market.side_effect = RuntimeError("exchange offline")
    failed = executor.execute_order("BTC", D("2"), D("100"), dry_run_first=False)
    assert failed.success is False and "offline" in failed.error
    assert len(executor.get_execution_history()) == 3
    exchange.fetch_order.side_effect = RuntimeError("offline")
    assert executor.verify_execution("missing") is None


def test_scheduled_strategy_waits_without_calling_exchange():
    executor = Mock()
    strategy = ScheduledExecutionStrategy(executor, datetime.now() + timedelta(hours=1))
    assert strategy.execute("BTC", D("1"), D("100")).success is False
    executor.execute_order.assert_not_called()
    strategy.execution_time = datetime.now() - timedelta(seconds=1)
    strategy.execute("BTC", D("1"), D("100"))
    executor.execute_order.assert_called_once()


def test_complete_cycle_aggregates_holdings_withdrawals_and_matches():
    dashboard = CompleteCycleDashboard()
    matches = [{"crypto_amount": 2, "crypto_currency": "USDC", "fiat_amount": 10, "fiat_currency": "BRL",
                "exchange_rate": 5, "confidence": 1, "time_delta_hours": 1}]
    result = dashboard.build_cycle_view(
        [{"asset": "USDC", "amount": 1, "cost_basis": 1}, {"asset": "USDC", "amount": 1, "cost_basis": 1}],
        [{"exchange": "binance", "connected": True}],
        [{"asset": "USDC", "amount": 2, "amount_in_usd": 2, "date_time": "2025-01-01", "tx_hash": "a" * 64, "status": "completed"}],
        [{"amount": 10, "currency": "BRL", "bank_type": "demo", "date": "2025-01-01"}], matches)
    stages = list(result.values())
    assert stages[0]["holdings"]["USDC"]["amount"] == 2
    assert stages[2]["total_withdrawn_usd"] == 2
    assert stages[3]["confirmed"] == 1
    assert stages[4]["by_currency"]["BRL"]["total"] == 10
    assert stages[5]["total_matches"] == 1
    assert "USDC" in dashboard.render_text_dashboard(result)
