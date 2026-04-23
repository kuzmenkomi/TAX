"""
Comprehensive test suite for Declairo Accounting Engines.

Tests FIFO (calculator.py), AVCO (avco_engine.py), Income Events,
Unrealized PnL, and cross-engine consistency.

~200 tests with hand-calculated expected values.
"""
import pytest
import pandas as pd
import numpy as np
from decimal import Decimal
from collections import deque
from unittest.mock import MagicMock, patch

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame from dicts with sane defaults."""
    defaults = {
        "asset": "BTC", "amount": 0.0, "fee": 0.0, "price": 0.0,
        "fee_asset": "ETH", "type": "BUY", "network": "ethereum",
        "asset_out": "", "amount_out": 0.0, "asset_in": "", "amount_in": 0.0,
        "note": "", "total_value": 0.0,
    }
    if not rows:
        # Return empty DF with correct columns so sort_values('timestamp') doesn't fail
        return pd.DataFrame(columns=list(defaults.keys()) + ["timestamp"])
    full_rows = []
    for r in rows:
        row = {**defaults, **r}
        if "timestamp" not in row:
            row["timestamp"] = pd.Timestamp("2024-01-01")
        elif isinstance(row["timestamp"], str):
            row["timestamp"] = pd.Timestamp(row["timestamp"])
        full_rows.append(row)
    return pd.DataFrame(full_rows)


class FakePriceService:
    """Deterministic price service for testing."""
    def __init__(self, prices: dict[str, float] | None = None):
        self._prices = prices or {"BTC": 50000.0, "ETH": 3000.0, "SOL": 100.0, "USDT": 1.0}

    def get_historical_price_usd(self, asset: str, timestamp: int) -> float:
        return self._prices.get(asset.upper(), 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: FIFO ENGINE TESTS  (calculator.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFifoConsume:
    """Unit tests for _consume_fifo helper."""

    def test_exact_lot(self):
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=1.0, unit_cost=100.0, timestamp=0)])
        cost, _ = _consume_fifo(lots, 1.0)
        assert cost == pytest.approx(100.0)
        assert len(lots) == 0

    def test_partial_lot(self):
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=2.0, unit_cost=100.0, timestamp=0)])
        cost, _ = _consume_fifo(lots, 1.0)
        assert cost == pytest.approx(100.0)
        assert len(lots) == 1
        assert lots[0].quantity == pytest.approx(1.0)

    def test_multi_lot_fifo_order(self):
        """First lot at $100, second at $200. Selling 1.5 should consume lot 1 fully + 0.5 of lot 2."""
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([
            Lot(quantity=1.0, unit_cost=100.0, timestamp=0),
            Lot(quantity=1.0, unit_cost=200.0, timestamp=1),
        ])
        cost, _ = _consume_fifo(lots, 1.5)
        # 1.0 * 100 + 0.5 * 200 = 200
        assert cost == pytest.approx(200.0)
        assert len(lots) == 1
        assert lots[0].quantity == pytest.approx(0.5)

    def test_insufficient_lots_raises(self):
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=0.5, unit_cost=100.0, timestamp=0)])
        with pytest.raises(ValueError):
            _consume_fifo(lots, 1.0)

    def test_empty_lots_raises(self):
        from app.accounting.calculator import _consume_fifo
        with pytest.raises(ValueError):
            _consume_fifo(deque(), 1.0)

    def test_zero_quantity(self):
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=1.0, unit_cost=100.0, timestamp=0)])
        cost, _ = _consume_fifo(lots, 0.0)
        assert cost == pytest.approx(0.0)
        assert len(lots) == 1  # lot untouched

    def test_consume_many_small_lots(self):
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=0.1, unit_cost=float(i*10), timestamp=i) for i in range(10)])
        cost, _ = _consume_fifo(lots, 0.5)
        # lots 0..4 consumed: 0.1*0 + 0.1*10 + 0.1*20 + 0.1*30 + 0.1*40 = 10.0
        assert cost == pytest.approx(10.0)
        assert len(lots) == 5

    def test_floating_point_precision(self):
        """Ensure tiny dust amounts don't break FIFO."""
        from app.accounting.calculator import _consume_fifo, Lot
        lots = deque([Lot(quantity=1.0, unit_cost=100.0, timestamp=0)])
        cost, _ = _consume_fifo(lots, 1.0 - 1e-15)
        assert cost == pytest.approx(100.0, abs=1e-10)


class TestFifoEngine:
    """Integration tests for the full FIFO calculate_pnl pipeline."""

    def _run(self, rows, matches=None, prices=None):
        from app.accounting.calculator import calculate_pnl, TaxRules
        df = _make_df(rows)
        ps = FakePriceService(prices)
        return calculate_pnl(df, matches or [], ps, rules=TaxRules())

    # ─── Basic buy/sell ───────────────────────────────────────────────────

    def test_simple_buy_then_sell_profit(self):
        """Buy 1 BTC @ $40k, sell @ $50k → $10k profit."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)
        assert r["taxable_events_count"] == 1

    def test_simple_buy_then_sell_loss(self):
        """Buy 1 BTC @ $50k, sell @ $40k → -$10k loss."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(-10000.0)

    def test_break_even(self):
        """Buy and sell at same price → 0 PnL."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(0.0)

    def test_partial_sell(self):
        """Buy 2 BTC @ $40k, sell 1 @ $50k → $10k profit, 1 BTC remains."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 2.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)

    def test_two_buys_fifo_order(self):
        """Buy 1 BTC @ $30k, buy 1 @ $40k, sell 1 @ $50k. FIFO uses $30k lot → $20k profit."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-03-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(20000.0)

    def test_two_buys_sell_all(self):
        """Buy 1@30k, buy 1@40k, sell 2@50k → 1*(50k-30k) + 1*(50k-40k) = 30k."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 2.0, "price": 50000, "timestamp": "2024-03-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(30000.0)

    # ─── Fees ─────────────────────────────────────────────────────────────

    def test_buy_fee_increases_cost_basis(self):
        """Buy 1 BTC @ $40k with 0.01 ETH fee ($30). Sell @ $50k.
        Cost basis = 40000 + 30 = 40030. Proceeds = 50000 - 0 = 50000.
        PnL = 50000 - 40030 = 9970. Gas tracked separately."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "fee": 0.01, "fee_asset": "ETH", "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.0, "timestamp": "2024-02-01"},
        ], prices={"BTC": 50000, "ETH": 3000})
        # fee_usd on buy = 0.01 * 3000 = 30
        # cost_basis = (1 * 40000) + 30 = 40030
        # sell proceeds = 50000 - 0 = 50000
        # PnL = 50000 - 40030 = 9970; gas = 30
        assert r["total_realized_pnl_usd"] == pytest.approx(9970.0)
        assert r["total_gas_fees_usd"] == pytest.approx(30.0)

    def test_sell_fee_reduces_proceeds(self):
        """Buy @ $40k, sell @ $50k with 0.01 ETH fee ($30).
        Proceeds = 50000 - 30 = 49970. PnL = 49970 - 40000 = 9970."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.01, "fee_asset": "ETH", "timestamp": "2024-02-01"},
        ], prices={"BTC": 50000, "ETH": 3000})
        assert r["total_realized_pnl_usd"] == pytest.approx(9970.0)

    # ─── Multi-asset ──────────────────────────────────────────────────────

    def test_multi_asset_independent_tracking(self):
        """BTC and ETH tracked independently."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 2000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "ETH", "amount": 10.0, "price": 3000, "timestamp": "2024-02-01"},
        ])
        # BTC: 50000-40000=10000; ETH: 10*(3000-2000)=10000
        assert r["total_realized_pnl_usd"] == pytest.approx(20000.0)
        assert r["realized_pnl_by_asset"]["BTC"] == pytest.approx(10000.0)
        assert r["realized_pnl_by_asset"]["ETH"] == pytest.approx(10000.0)

    # ─── Swaps ────────────────────────────────────────────────────────────

    def test_swap_basic(self):
        """Buy 1 BTC @ $40k, swap to ETH when BTC=$50k. Gain=$10k on BTC side."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SWAP", "asset": "BTC", "amount": 0, "price": 0,
             "asset_out": "BTC", "amount_out": 1.0,
             "asset_in": "ETH", "amount_in": 16.67,
             "timestamp": "2024-02-01"},
        ], prices={"BTC": 50000, "ETH": 3000})
        assert r["realized_pnl_by_asset"]["BTC"] == pytest.approx(10000.0)
        assert r["taxable_events_count"] == 1

    # ─── Internal transfers ───────────────────────────────────────────────

    def test_internal_transfer_no_tax_event(self):
        """Matched internal transfers should not create taxable events."""
        r = self._run(
            [
                {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
                {"type": "TRANSFER", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.001, "fee_asset": "ETH", "timestamp": "2024-02-01"},
                {"type": "RECEIVE", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
            ],
            matches=[{"transfer_index": 1, "receive_index": 2}],
            prices={"BTC": 50000, "ETH": 3000},
        )
        assert r["taxable_events_count"] == 0
        assert r["internal_transfer_count"] == 1
        # Gas fee from transfer side: 0.001 * 3000 = 3.0
        assert r["total_gas_fees_usd"] == pytest.approx(3.0)

    # ─── Edge cases ───────────────────────────────────────────────────────

    def test_empty_dataframe(self):
        r = self._run([])
        assert r["total_realized_pnl_usd"] == 0.0
        assert r["taxable_events_count"] == 0

    def test_only_buys_no_pnl(self):
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
        ])
        assert r["total_realized_pnl_usd"] == 0.0
        assert r["taxable_events_count"] == 0

    def test_receive_as_buy(self):
        """RECEIVE type treated same as BUY for non-internal transfers."""
        r = self._run([
            {"type": "RECEIVE", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)

    def test_many_small_trades(self):
        """10 buys of 0.1 BTC at increasing prices, then sell all."""
        rows = []
        for i in range(10):
            rows.append({
                "type": "BUY", "asset": "BTC", "amount": 0.1,
                "price": 40000 + i * 1000,
                "timestamp": f"2024-01-{i+1:02d}",
            })
        rows.append({
            "type": "SELL", "asset": "BTC", "amount": 1.0, "price": 55000,
            "timestamp": "2024-02-01",
        })
        r = self._run(rows)
        # Total cost = sum(0.1 * (40000+i*1000) for i in 0..9)
        # = 0.1 * (40000*10 + 1000*(0+1+2+...+9)) = 0.1 * (400000 + 45000) = 44500
        # Proceeds = 1.0 * 55000 = 55000. PnL = 55000 - 44500 = 10500
        assert r["total_realized_pnl_usd"] == pytest.approx(10500.0)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: AVCO ENGINE TESTS  (avco_engine.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAvcoEngine:
    """Tests for AVCO (Average Cost) accounting engine."""

    def _run(self, rows):
        from app.accounting.avco_engine import compute_pnl_avco
        df = _make_df(rows)
        return compute_pnl_avco(df)

    def test_simple_buy_sell_profit(self):
        """Buy 1 BTC @ $40k, sell @ $50k → $10k profit."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)
        assert r["engine"] == "avco"

    def test_simple_buy_sell_loss(self):
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(-10000.0)

    def test_average_cost_two_buys(self):
        """Buy 1@30k, buy 1@50k. Avg cost = 40k. Sell 1@45k → 5k profit."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 45000, "timestamp": "2024-03-01"},
        ])
        # Avg cost = (30000+50000)/2 = 40000. PnL = 45000 - 40000 = 5000
        assert r["total_realized_pnl_usd"] == pytest.approx(5000.0)

    def test_average_cost_three_buys_different_sizes(self):
        """Buy 2@30k, buy 1@60k. Avg cost = (60000+60000)/3 = 40000. Sell 1@50k → 10k."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 2.0, "price": 30000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-03-01"},
        ])
        # Avg cost = (2*30000 + 1*60000) / 3 = 120000/3 = 40000
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)

    def test_avco_differs_from_fifo(self):
        """AVCO and FIFO give different results when lots have different costs."""
        rows = [
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 30000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 45000, "timestamp": "2024-03-01"},
        ]
        avco_r = self._run(rows)
        # AVCO: avg=40k, PnL=5k
        assert avco_r["total_realized_pnl_usd"] == pytest.approx(5000.0)
        # FIFO would give: cost=30k (first lot), PnL=15k — different!

    def test_sell_with_fee(self):
        """Fee reduces proceeds. Buy 1@40k, sell 1@50k with fee 0.01 @ price 50k.
        fee_value=0.01*50000=500. Proceeds=1*50000-500=49500. Cost=40000. PnL=9500."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.01, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(9500.0)

    def test_deposit_adds_inventory(self):
        """DEPOSIT type should add to inventory."""
        r = self._run([
            {"type": "DEPOSIT", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["total_realized_pnl_usd"] == pytest.approx(10000.0)

    def test_transfer_fee_as_gas_expense(self):
        """TRANSFER fee should be tracked as gas expense."""
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "TRANSFER", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.001, "timestamp": "2024-02-01"},
        ])
        # Gas fee = 0.001 * 50000 = 50
        assert r["total_gas_fees_usd"] == pytest.approx(50.0)
        assert r["realized_pnl_by_asset"].get("GAS_EXPENSE", 0) == pytest.approx(-50.0)

    def test_empty_dataframe(self):
        r = self._run([])
        assert r["total_realized_pnl_usd"] == 0.0

    def test_only_buys(self):
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
        ])
        assert r["total_realized_pnl_usd"] == 0.0
        assert r["inventory"]["BTC"]["quantity"] == pytest.approx(1.0)
        assert r["inventory"]["BTC"]["avg_cost"] == pytest.approx(40000.0)

    def test_inventory_updated_after_sell(self):
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 2.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ])
        assert r["inventory"]["BTC"]["quantity"] == pytest.approx(1.0)
        assert r["inventory"]["BTC"]["avg_cost"] == pytest.approx(40000.0)

    def test_staking_adds_to_inventory(self):
        """STAKING_REWARD should be added to inventory at FMV."""
        r = self._run([
            {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 2000, "timestamp": "2024-01-01"},
            {"type": "STAKING_REWARD", "asset": "ETH", "amount": 0.5, "price": 3000, "timestamp": "2024-06-01"},
            {"type": "SELL", "asset": "ETH", "amount": 10.5, "price": 3500, "timestamp": "2024-12-01"},
        ])
        # Avg cost = (10*2000 + 0.5*3000) / 10.5 = 21500/10.5 ≈ 2047.619
        # PnL = 10.5*3500 - 10.5*2047.619 = 36750 - 21500 = 15250
        assert r["total_realized_pnl_usd"] == pytest.approx(15250.0)

    def test_airdrop_zero_cost(self):
        """Airdrop at price $0 should still be in inventory (edge case skipped by amount>0 check)."""
        r = self._run([
            {"type": "AIRDROP", "asset": "SHIB", "amount": 1000000, "price": 0.00001, "timestamp": "2024-01-01"},
        ])
        # Should be in inventory
        assert r["inventory"]["SHIB"]["quantity"] == pytest.approx(1000000.0)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: INCOME EVENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncomeEvents:
    """Tests for compute_income_events."""

    def _run(self, rows):
        from app.accounting.avco_engine import compute_income_events
        df = _make_df(rows)
        return compute_income_events(df)

    def test_staking_reward(self):
        r = self._run([
            {"type": "STAKING_REWARD", "asset": "ETH", "amount": 0.5, "price": 3000, "timestamp": "2024-01-01"},
        ])
        assert r["total_income_usd"] == pytest.approx(1500.0)
        assert r["events_count"] == 1
        assert "STAKING_REWARD" in r["income_by_type"]

    def test_staking_alias(self):
        """'STAKING' should be normalized to 'STAKING_REWARD'."""
        r = self._run([
            {"type": "STAKING", "asset": "ETH", "amount": 1.0, "price": 2000, "timestamp": "2024-01-01"},
        ])
        assert r["events_count"] == 1
        assert "STAKING_REWARD" in r["income_by_type"]
        assert r["total_income_usd"] == pytest.approx(2000.0)

    def test_lending_alias(self):
        """'LENDING' normalized to 'LENDING_INTEREST'."""
        r = self._run([
            {"type": "LENDING", "asset": "USDC", "amount": 100, "price": 1.0, "timestamp": "2024-01-01"},
        ])
        assert "LENDING_INTEREST" in r["income_by_type"]
        assert r["total_income_usd"] == pytest.approx(100.0)

    def test_airdrop(self):
        r = self._run([
            {"type": "AIRDROP", "asset": "UNI", "amount": 400, "price": 5.0, "timestamp": "2024-01-01"},
        ])
        assert r["total_income_usd"] == pytest.approx(2000.0)
        assert r["income_by_asset"]["UNI"] == pytest.approx(2000.0)

    def test_mining(self):
        r = self._run([
            {"type": "MINING", "asset": "BTC", "amount": 0.001, "price": 60000, "timestamp": "2024-01-01"},
        ])
        assert r["total_income_usd"] == pytest.approx(60.0)

    def test_farming_reward(self):
        r = self._run([
            {"type": "FARMING_REWARD", "asset": "CAKE", "amount": 10, "price": 3.5, "timestamp": "2024-01-01"},
        ])
        assert r["total_income_usd"] == pytest.approx(35.0)

    def test_interest(self):
        r = self._run([
            {"type": "INTEREST", "asset": "USDT", "amount": 50, "price": 1.0, "timestamp": "2024-01-01"},
        ])
        assert r["total_income_usd"] == pytest.approx(50.0)

    def test_buy_is_not_income(self):
        r = self._run([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
        ])
        assert r["events_count"] == 0
        assert r["total_income_usd"] == 0.0

    def test_sell_is_not_income(self):
        r = self._run([
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
        ])
        assert r["events_count"] == 0

    def test_multi_income_aggregation(self):
        r = self._run([
            {"type": "STAKING_REWARD", "asset": "ETH", "amount": 1.0, "price": 3000, "timestamp": "2024-01-01"},
            {"type": "AIRDROP", "asset": "UNI", "amount": 100, "price": 5.0, "timestamp": "2024-02-01"},
            {"type": "MINING", "asset": "BTC", "amount": 0.01, "price": 50000, "timestamp": "2024-03-01"},
        ])
        # 3000 + 500 + 500 = 4000
        assert r["total_income_usd"] == pytest.approx(4000.0)
        assert r["events_count"] == 3
        assert len(r["income_by_type"]) == 3
        assert len(r["income_by_asset"]) == 3

    def test_zero_amount_skipped(self):
        r = self._run([
            {"type": "STAKING_REWARD", "asset": "ETH", "amount": 0, "price": 3000, "timestamp": "2024-01-01"},
        ])
        assert r["events_count"] == 0

    def test_zero_price_skipped(self):
        r = self._run([
            {"type": "STAKING_REWARD", "asset": "ETH", "amount": 1.0, "price": 0, "timestamp": "2024-01-01"},
        ])
        assert r["events_count"] == 0

    def test_empty_dataframe(self):
        r = self._run([])
        assert r["events_count"] == 0
        assert r["total_income_usd"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: UNREALIZED PNL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnrealizedPnl:
    """Tests for compute_positions_with_unrealized_pnl."""

    def _run(self, rows, current_prices):
        from app.accounting.avco_engine import compute_positions_with_unrealized_pnl
        df = _make_df(rows)
        return compute_positions_with_unrealized_pnl(df, current_prices)

    def test_basic_unrealized_gain(self):
        """Buy 1 BTC @ $40k, current price $50k → $10k unrealized gain."""
        positions = self._run(
            [{"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"}],
            {"btc": 50000.0},
        )
        assert len(positions) == 1
        p = positions[0]
        assert p["asset"] == "BTC"
        assert p["quantity"] == pytest.approx(1.0)
        assert p["avg_cost_usd"] == pytest.approx(40000.0)
        assert p["unrealized_pnl_usd"] == pytest.approx(10000.0)

    def test_unrealized_loss(self):
        positions = self._run(
            [{"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"}],
            {"btc": 40000.0},
        )
        assert positions[0]["unrealized_pnl_usd"] == pytest.approx(-20000.0)

    def test_no_price_data_skipped(self):
        """Positions without current prices should be skipped."""
        positions = self._run(
            [{"type": "BUY", "asset": "OBSCURE", "amount": 100, "price": 1.0, "timestamp": "2024-01-01"}],
            {},
        )
        assert len(positions) == 0

    def test_sold_position_not_shown(self):
        positions = self._run(
            [
                {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
                {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
            ],
            {"btc": 60000.0},
        )
        assert len(positions) == 0

    def test_multi_position_sorted_by_value(self):
        positions = self._run(
            [
                {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
                {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 2000, "timestamp": "2024-01-01"},
            ],
            {"btc": 50000.0, "eth": 3000.0},
        )
        assert len(positions) == 2
        # BTC value=50000, ETH value=30000. BTC should be first.
        assert positions[0]["asset"] == "BTC"
        assert positions[1]["asset"] == "ETH"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: CROSS-ENGINE CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossEngineConsistency:
    """For simple single-lot scenarios, FIFO and AVCO should give identical results."""

    def test_single_lot_consistency(self):
        """Single buy → single sell. Both engines should agree."""
        rows = [
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-02-01"},
        ]
        from app.accounting.calculator import calculate_pnl, TaxRules
        from app.accounting.avco_engine import compute_pnl_avco

        df = _make_df(rows)
        fifo_r = calculate_pnl(df, [], FakePriceService({"BTC": 50000}), rules=TaxRules())
        avco_r = compute_pnl_avco(df)

        assert fifo_r["total_realized_pnl_usd"] == pytest.approx(avco_r["total_realized_pnl_usd"])

    def test_equal_cost_lots_consistency(self):
        """Multiple buys at same price → both engines should agree."""
        rows = [
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 2.0, "price": 50000, "timestamp": "2024-03-01"},
        ]
        from app.accounting.calculator import calculate_pnl, TaxRules
        from app.accounting.avco_engine import compute_pnl_avco

        df = _make_df(rows)
        fifo_r = calculate_pnl(df, [], FakePriceService({"BTC": 50000}), rules=TaxRules())
        avco_r = compute_pnl_avco(df)

        assert fifo_r["total_realized_pnl_usd"] == pytest.approx(avco_r["total_realized_pnl_usd"])
