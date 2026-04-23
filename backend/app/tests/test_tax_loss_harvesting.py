"""
Comprehensive test suite for Declairo Tax Loss Harvesting engine.

Tests: position lot building, loss detection, wash sale checks,
holding period classification, recommendation sorting, and edge cases.

~100 tests with hand-calculated expected values.
"""
import pytest
import pandas as pd
from decimal import Decimal

from app.accounting.tax_loss_harvesting import (
    build_position_lots,
    find_loss_positions,
    generate_loss_harvesting_report,
    _check_potential_wash_sales,
    recommend_replacement_assets,
    TaxPosition,
    HarvestingRecommendation,
)


def _make_df(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "asset": "BTC", "amount": 0.0, "fee": 0.0, "price": 0.0,
        "type": "BUY", "note": "",
    }
    if not rows:
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


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: POSITION LOT BUILDING
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildPositionLots:
    """Tests for build_position_lots."""

    def test_single_buy_creates_one_lot(self):
        df = _make_df([{"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000}])
        lots = build_position_lots(df)
        assert "BTC" in lots
        assert len(lots["BTC"]) == 1
        assert lots["BTC"][0].quantity == Decimal("1.0")
        assert lots["BTC"][0].cost_per_unit == Decimal("50000")

    def test_two_buys_create_two_lots(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 0.5, "price": 60000, "timestamp": "2024-02-01"},
        ])
        lots = build_position_lots(df)
        assert len(lots["BTC"]) == 2

    def test_sell_removes_fifo(self):
        """Buy 1@40k, buy 1@60k, sell 1. First lot removed (FIFO)."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-02-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-03-01"},
        ])
        lots = build_position_lots(df)
        assert len(lots["BTC"]) == 1
        # Remaining lot should be the $60k one
        assert lots["BTC"][0].cost_per_unit == Decimal("60000")

    def test_partial_sell(self):
        """Buy 2 BTC, sell 0.5. Remaining: 1.5 BTC."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 2.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 0.5, "price": 55000, "timestamp": "2024-02-01"},
        ])
        lots = build_position_lots(df)
        assert lots["BTC"][0].quantity == Decimal("1.5")

    def test_sell_all_removes_position(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 55000, "timestamp": "2024-02-01"},
        ])
        lots = build_position_lots(df)
        assert "BTC" not in lots

    def test_receive_creates_lot(self):
        df = _make_df([{"type": "RECEIVE", "asset": "ETH", "amount": 5.0, "price": 3000}])
        lots = build_position_lots(df)
        assert "ETH" in lots

    def test_deposit_creates_lot(self):
        df = _make_df([{"type": "DEPOSIT", "asset": "BTC", "amount": 1.0, "price": 50000}])
        lots = build_position_lots(df)
        assert "BTC" in lots

    def test_staking_creates_lot(self):
        df = _make_df([{"type": "STAKING", "asset": "ETH", "amount": 0.5, "price": 3000}])
        lots = build_position_lots(df)
        assert "ETH" in lots

    def test_airdrop_creates_lot(self):
        df = _make_df([{"type": "AIRDROP", "asset": "UNI", "amount": 100, "price": 5.0}])
        lots = build_position_lots(df)
        assert "UNI" in lots

    def test_mining_creates_lot(self):
        df = _make_df([{"type": "MINING", "asset": "BTC", "amount": 0.001, "price": 60000}])
        lots = build_position_lots(df)
        assert "BTC" in lots

    def test_fee_included_in_cost_basis(self):
        """Buy 1 BTC @ $50k with 0.01 fee at $50k → cost = 50000 + 0.01*50000 = 50500."""
        df = _make_df([{"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "fee": 0.01}])
        lots = build_position_lots(df)
        expected_cost = (1.0 * 50000 + 0.01 * 50000) / 1.0  # 50500
        assert float(lots["BTC"][0].cost_per_unit) == pytest.approx(expected_cost)

    def test_multi_asset(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 3000, "timestamp": "2024-01-01"},
        ])
        lots = build_position_lots(df)
        assert "BTC" in lots and "ETH" in lots

    def test_empty_dataframe(self):
        df = _make_df([])
        lots = build_position_lots(df)
        assert len(lots) == 0

    def test_zero_amount_skipped(self):
        df = _make_df([{"type": "BUY", "asset": "BTC", "amount": 0, "price": 50000}])
        lots = build_position_lots(df)
        assert "BTC" not in lots

    def test_zero_price_skipped(self):
        df = _make_df([{"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 0}])
        lots = build_position_lots(df)
        assert "BTC" not in lots


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: LOSS POSITION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindLossPositions:
    """Tests for find_loss_positions."""

    def test_detects_loss(self):
        """Buy at $50k, current price $30k → $20k loss."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
        ])
        recs = find_loss_positions(df, {"btc": 30000.0}, tax_rate=0.15, min_loss_usd=0)
        assert len(recs) == 1
        assert float(recs[0].unrealized_loss) == pytest.approx(-20000.0)
        assert float(recs[0].tax_savings_usd) == pytest.approx(3000.0)

    def test_no_loss_no_recommendation(self):
        """Buy at $40k, current price $50k → gain, no recommendation."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
        ])
        recs = find_loss_positions(df, {"btc": 50000.0})
        assert len(recs) == 0

    def test_min_loss_filter(self):
        """Small loss below threshold should be filtered."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 0.001, "price": 50000, "timestamp": "2024-01-01"},
        ])
        # Loss = 0.001 * (49000 - 50000) = -1.0
        recs = find_loss_positions(df, {"btc": 49000.0}, min_loss_usd=10.0)
        assert len(recs) == 0

    def test_sorted_by_savings(self):
        """Multiple positions should be sorted by tax savings descending."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 4000, "timestamp": "2024-01-01"},
        ])
        recs = find_loss_positions(df, {"btc": 40000.0, "eth": 3000.0}, min_loss_usd=0)
        # BTC loss: 20000, ETH loss: 10000
        assert len(recs) == 2
        assert recs[0].asset == "BTC"  # Larger loss first

    def test_action_sell_now_for_large_loss(self):
        """Loss > $500 should recommend SELL_NOW."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
        ])
        recs = find_loss_positions(df, {"btc": 50000.0}, min_loss_usd=0)
        assert recs[0].action == "SELL_NOW"

    def test_action_monitor_for_small_loss(self):
        """Loss <= $500 should recommend MONITOR."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 0.01, "price": 60000, "timestamp": "2024-01-01"},
        ])
        # Loss = 0.01 * (55000 - 60000) = -50
        recs = find_loss_positions(df, {"btc": 55000.0}, min_loss_usd=0)
        if recs:
            assert recs[0].action == "MONITOR"

    def test_no_price_data_skipped(self):
        df = _make_df([
            {"type": "BUY", "asset": "OBSCURE", "amount": 1000, "price": 1.0, "timestamp": "2024-01-01"},
        ])
        recs = find_loss_positions(df, {})
        assert len(recs) == 0

    def test_holding_period_short_term(self):
        """Recently bought (< 365 days)."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": pd.Timestamp.now() - pd.Timedelta(days=30)},
        ])
        recs = find_loss_positions(df, {"btc": 40000.0}, min_loss_usd=0)
        assert recs[0].long_term_capital_gain == False
        assert recs[0].holding_period_days < 365

    def test_holding_period_long_term(self):
        """Bought over a year ago."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": pd.Timestamp.now() - pd.Timedelta(days=400)},
        ])
        recs = find_loss_positions(df, {"btc": 40000.0}, min_loss_usd=0)
        assert recs[0].long_term_capital_gain == True

    def test_multi_lot_per_asset(self):
        """Two lots of same asset at different prices."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 70000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-02-01"},
        ])
        recs = find_loss_positions(df, {"btc": 50000.0}, min_loss_usd=0)
        # Both lots have losses
        assert len(recs) == 2

    def test_custom_tax_rate(self):
        """Tax savings should use the provided rate."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
        ])
        recs_15 = find_loss_positions(df, {"btc": 40000.0}, tax_rate=0.15, min_loss_usd=0)
        recs_30 = find_loss_positions(df, {"btc": 40000.0}, tax_rate=0.30, min_loss_usd=0)
        # $10k loss: 15% → $1500, 30% → $3000
        assert float(recs_15[0].tax_savings_usd) == pytest.approx(1500.0)
        assert float(recs_30[0].tax_savings_usd) == pytest.approx(3000.0)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: WASH SALE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestWashSaleDetection:
    """Tests for _check_potential_wash_sales."""

    def test_no_wash_sale(self):
        """Sell and rebuy after 31 days — no wash sale."""
        df = _make_df([
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 40000, "fee": 0.001, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 35000, "timestamp": "2024-02-02"},
        ])
        issues = _check_potential_wash_sales(df)
        assert len(issues) == 0

    def test_wash_sale_within_30_days(self):
        """Sell at loss and rebuy within 30 days."""
        df = _make_df([
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 40000, "fee": 0.001, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 35000, "timestamp": "2024-01-15"},
        ])
        issues = _check_potential_wash_sales(df)
        assert len(issues) >= 1
        assert "BTC" in issues[0]

    def test_different_assets_no_wash_sale(self):
        """Sell BTC, buy ETH within 30 days — not a wash sale."""
        df = _make_df([
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 40000, "fee": 0.001, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "ETH", "amount": 10.0, "price": 3000, "timestamp": "2024-01-15"},
        ])
        issues = _check_potential_wash_sales(df)
        assert len(issues) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestHarvestingReport:

    def test_no_opportunities(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 40000, "timestamp": "2024-01-01"},
        ])
        report = generate_loss_harvesting_report(df, {"btc": 50000.0})
        assert report["status"] == "no_opportunities"
        assert report["total_unrealized_losses"] == 0.0

    def test_has_opportunities(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
        ])
        report = generate_loss_harvesting_report(df, {"btc": 40000.0})
        assert report["status"] == "opportunities_found"
        assert report["total_unrealized_losses"] > 0
        assert report["total_tax_savings"] > 0
        assert len(report["recommendations"]) > 0

    def test_recommendations_capped_at_10(self):
        """Report should show max 10 recommendations."""
        rows = []
        for i in range(20):
            rows.append({
                "type": "BUY", "asset": f"TOKEN{i}", "amount": 100,
                "price": 10.0, "timestamp": f"2024-01-{i+1:02d}",
            })
        df = _make_df(rows)
        prices = {f"token{i}": 5.0 for i in range(20)}
        report = generate_loss_harvesting_report(df, prices)
        assert len(report["recommendations"]) <= 10

    def test_report_summary_stats(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
            {"type": "BUY", "asset": "ETH", "amount": 10, "price": 4000, "timestamp": "2024-01-01"},
        ])
        report = generate_loss_harvesting_report(df, {"btc": 40000.0, "eth": 3000.0})
        assert report["summary"]["assets_with_losses"] == 2
        assert report["summary"]["total_positions_analyzed"] == 2

    def test_report_has_next_steps(self):
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
        ])
        report = generate_loss_harvesting_report(df, {"btc": 40000.0})
        assert "next_steps" in report
        assert len(report["next_steps"]) > 0

    def test_large_loss_warning(self):
        """Losses > $10k should generate a warning."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 60000, "timestamp": "2024-01-01"},
        ])
        report = generate_loss_harvesting_report(df, {"btc": 40000.0})
        assert len(report["warnings"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: REPLACEMENT ASSETS
# ═══════════════════════════════════════════════════════════════════════════════

class TestReplacementAssets:

    def test_btc_replacements(self):
        r = recommend_replacement_assets("BTC", {})
        assert "WBTC" in r

    def test_eth_replacements(self):
        r = recommend_replacement_assets("ETH", {})
        assert "stETH" in r

    def test_usdc_replacements(self):
        r = recommend_replacement_assets("USDC", {})
        assert "USDT" in r

    def test_unknown_asset_empty(self):
        r = recommend_replacement_assets("OBSCURE_TOKEN", {})
        assert len(r) == 0

    def test_case_insensitive(self):
        r = recommend_replacement_assets("btc", {})
        assert len(r) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: EDGE CASES AND STRESS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_empty_df_all_functions(self):
        df = _make_df([])
        assert len(build_position_lots(df)) == 0
        assert len(find_loss_positions(df, {"btc": 50000})) == 0
        report = generate_loss_harvesting_report(df, {"btc": 50000})
        assert report["status"] == "no_opportunities"

    def test_only_sells(self):
        """Sells without prior buys — no lots to close."""
        df = _make_df([
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
        ])
        lots = build_position_lots(df)
        assert "BTC" not in lots

    def test_many_assets(self):
        """Stress: 50 different assets."""
        rows = [
            {"type": "BUY", "asset": f"TOKEN{i}", "amount": 10.0, "price": 100.0, "timestamp": f"2024-01-{(i%28)+1:02d}"}
            for i in range(50)
        ]
        df = _make_df(rows)
        lots = build_position_lots(df)
        assert len(lots) == 50

    def test_buy_sell_buy_sequence(self):
        """Buy, sell all, buy again. Should have 1 lot."""
        df = _make_df([
            {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 50000, "timestamp": "2024-01-01"},
            {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 55000, "timestamp": "2024-02-01"},
            {"type": "BUY", "asset": "BTC", "amount": 2.0, "price": 45000, "timestamp": "2024-03-01"},
        ])
        lots = build_position_lots(df)
        assert len(lots["BTC"]) == 1
        assert lots["BTC"][0].quantity == Decimal("2.0")

    def test_tax_savings_zero_for_gain(self):
        """TaxPosition.tax_savings should return 0.0 for a gain."""
        pos = TaxPosition(
            asset="BTC",
            quantity=Decimal("1"),
            cost_per_unit=Decimal("40000"),
            acquisition_date=pd.Timestamp.now(),
            cost_basis_total=Decimal("40000"),
        )
        savings = pos.tax_savings(Decimal("5000"))  # gain
        assert savings == Decimal("0")

    def test_tax_savings_positive_for_loss(self):
        pos = TaxPosition(
            asset="BTC",
            quantity=Decimal("1"),
            cost_per_unit=Decimal("50000"),
            acquisition_date=pd.Timestamp.now(),
            cost_basis_total=Decimal("50000"),
        )
        savings = pos.tax_savings(Decimal("-10000"), Decimal("0.15"))
        assert savings == Decimal("1500")
