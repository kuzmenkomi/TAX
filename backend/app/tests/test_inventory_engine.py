"""Tests for FIFO/AVCO inventory consistency on open positions."""

import pytest

from app.accounting.avco_engine import compute_positions_with_unrealized_pnl
from app.accounting.inventory_engine import compute_open_inventory
from app.tests.test_accounting_engines import _make_df


class TestInventoryEngine:
    def test_fifo_and_avco_differ_after_partial_sell(self):
        rows = [
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30_000, "total_value": 30_000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50_000, "total_value": 50_000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 60_000, "total_value": 60_000, "timestamp": "2024-03-01"},
        ]
        df = _make_df(rows)
        avco = compute_open_inventory(df, "AVCO")
        fifo = compute_open_inventory(df, "FIFO")

        assert avco["BTC"]["quantity"] == pytest.approx(1.0)
        assert fifo["BTC"]["quantity"] == pytest.approx(1.0)
        # AVCO keeps blended cost; FIFO keeps the newer (Feb) lot after selling oldest.
        assert avco["BTC"]["avg_cost"] == pytest.approx(40_000.0)
        assert fifo["BTC"]["avg_cost"] == pytest.approx(50_000.0)

    def test_positions_respect_accounting_method(self):
        df = _make_df(
            [
                {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30_000, "total_value": 30_000, "timestamp": "2024-01-01"},
                {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50_000, "total_value": 50_000, "timestamp": "2024-02-01"},
                {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 60_000, "total_value": 60_000, "timestamp": "2024-03-01"},
            ]
        )
        prices = {"btc": 55_000.0}
        avco_positions = compute_positions_with_unrealized_pnl(df, prices, "AVCO")
        fifo_positions = compute_positions_with_unrealized_pnl(df, prices, "FIFO")

        assert avco_positions[0]["unrealized_pnl_usd"] == pytest.approx(15_000.0)
        assert fifo_positions[0]["unrealized_pnl_usd"] == pytest.approx(5_000.0)
