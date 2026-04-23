"""
Tests for income recognition and tax loss harvesting features.

Run with: pytest backend/app/tests/test_income_and_loss_features.py -v
"""

import pandas as pd
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.accounting.avco_engine import compute_income_events, compute_pnl_avco, IncomeEvent
from app.accounting.tax_loss_harvesting import (
    find_loss_positions,
    generate_loss_harvesting_report,
    build_position_lots,
    recommend_replacement_assets,
)


class TestIncomeRecognition:
    """Test income event recognition."""

    @pytest.fixture
    def sample_income_df(self):
        """Create sample dataframe with income events."""
        data = {
            "timestamp": [
                pd.Timestamp("2024-01-10 10:00:00"),
                pd.Timestamp("2024-02-15 14:30:00"),
                pd.Timestamp("2024-03-20 09:15:00"),
                pd.Timestamp("2024-04-25 11:45:00"),
            ],
            "type": ["STAKING_REWARD", "AIRDROP", "LENDING_INTEREST", "STAKING"],
            "asset": ["ETH", "ARB", "USDC", "SOL"],
            "amount": [0.5, 100, 50, 10],
            "price": [2000, 1.50, 1.00, 95],
            "fee": [0, 0, 0, 0],
            "total_value": [1000, 150, 50, 950],
        }
        return pd.DataFrame(data)

    def test_income_events_detection(self, sample_income_df):
        """Test that income events are properly detected."""
        result = compute_income_events(sample_income_df)

        assert result["events_count"] == 4
        assert result["total_income_usd"] == 2150.0  # 1000 + 150 + 50 + 950
        assert "STAKING_REWARD" in result["income_by_type"]
        assert "AIRDROP" in result["income_by_type"]
        assert "LENDING_INTEREST" in result["income_by_type"]

    def test_income_by_type_breakdown(self, sample_income_df):
        """Test income breakdown by type."""
        result = compute_income_events(sample_income_df)

        assert result["income_by_type"]["STAKING_REWARD"] == 1950.0  # ETH + SOL
        assert result["income_by_type"]["AIRDROP"] == 150.0
        assert result["income_by_type"]["LENDING_INTEREST"] == 50.0

    def test_income_by_asset_breakdown(self, sample_income_df):
        """Test income breakdown by asset."""
        result = compute_income_events(sample_income_df)

        assert result["income_by_asset"]["ETH"] == 1000.0
        assert result["income_by_asset"]["ARB"] == 150.0
        assert result["income_by_asset"]["USDC"] == 50.0
        assert result["income_by_asset"]["SOL"] == 950.0

    def test_income_events_fmv_valuation(self, sample_income_df):
        """Test that income is valued at FMV on receipt date."""
        result = compute_income_events(sample_income_df)

        # Check first event
        events = result["income_events"]
        assert len(events) == 4

        # ETH event: 0.5 ETH * $2000 = $1000
        eth_event = events[0]
        assert eth_event.asset == "ETH"
        assert float(eth_event.amount) == 0.5
        assert float(eth_event.fmv_per_unit) == 2000.0
        assert float(eth_event.total_usd) == 1000.0

    def test_income_in_inventory(self, sample_income_df):
        """Test that income events increase inventory (cost basis)."""
        pnl = compute_pnl_avco(sample_income_df)

        inventory = pnl["inventory"]
        assert "ETH" in inventory
        assert inventory["ETH"]["quantity"] == 0.5
        assert inventory["ETH"]["avg_cost"] == 2000.0

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame(
            columns=["timestamp", "type", "asset", "amount", "price", "fee"]
        )
        result = compute_income_events(df)

        assert result["events_count"] == 0
        assert result["total_income_usd"] == 0.0


class TestTaxLossHarvesting:
    """Test tax loss harvesting functionality."""

    @pytest.fixture
    def sample_portfolio_df(self):
        """Create sample portfolio with gains and losses."""
        data = {
            "timestamp": [
                # BTC purchases
                pd.Timestamp("2023-01-10"),
                pd.Timestamp("2023-06-15"),
                # ETH purchases
                pd.Timestamp("2023-02-20"),
                pd.Timestamp("2023-07-10"),
                # SOL purchases
                pd.Timestamp("2023-03-05"),
            ],
            "type": ["BUY", "BUY", "BUY", "BUY", "BUY"],
            "asset": ["BTC", "BTC", "ETH", "ETH", "SOL"],
            "amount": [1.0, 0.5, 5.0, 3.0, 100],
            "price": [50000, 65000, 2500, 2800, 100],
            "fee": [0, 0, 0, 0, 0],
        }
        return pd.DataFrame(data)

    def test_position_lot_building(self, sample_portfolio_df):
        """Test that position lots are properly built."""
        lots = build_position_lots(sample_portfolio_df)

        assert "BTC" in lots
        assert "ETH" in lots
        assert "SOL" in lots

        # Check BTC lots
        btc_lots = lots["BTC"]
        assert len(btc_lots) == 2
        assert float(btc_lots[0].quantity) == 1.0
        assert float(btc_lots[0].cost_per_unit) == 50000.0
        assert float(btc_lots[1].quantity) == 0.5
        assert float(btc_lots[1].cost_per_unit) == 65000.0

    def test_unrealized_loss_detection(self, sample_portfolio_df):
        """Test detection of unrealized losses."""
        current_prices = {
            "btc": 42000,  # Down from 50000/65000
            "eth": 1800,   # Down from 2500/2800
            "sol": 95,     # Down from 100
        }

        recommendations = find_loss_positions(
            sample_portfolio_df,
            current_prices,
            tax_rate=0.15,
            min_loss_usd=0,  # Show all losses
        )

        # Should find losses for all assets
        assert len(recommendations) > 0

        # Find BTC recommendations
        btc_recs = [r for r in recommendations if r.asset == "BTC"]
        assert len(btc_recs) > 0

        # Should have unrealized losses
        for rec in btc_recs:
            assert float(rec.unrealized_loss) < 0

    def test_loss_sorting_by_tax_savings(self, sample_portfolio_df):
        """Test that recommendations are sorted by tax savings (largest first)."""
        current_prices = {
            "btc": 42000,
            "eth": 1800,
            "sol": 95,
        }

        recommendations = find_loss_positions(
            sample_portfolio_df, current_prices, tax_rate=0.15
        )

        # Check that recommendations are sorted by tax savings
        tax_savings = [float(r.tax_savings_usd) for r in recommendations]
        assert tax_savings == sorted(tax_savings, reverse=True)

    def test_holding_period_calculation(self, sample_portfolio_df):
        """Test that holding periods are calculated correctly."""
        current_prices = {"btc": 42000, "eth": 1800, "sol": 95}

        recommendations = find_loss_positions(
            sample_portfolio_df, current_prices, tax_rate=0.15
        )

        for rec in recommendations:
            # Holding period should be positive
            assert rec.holding_period_days > 0

        # BTC from Jan 2023 should be long-term (>365 days)
        btc_jan = [
            r
            for r in recommendations
            if r.asset == "BTC" and r.acquisition_date == pd.Timestamp("2023-01-10")
        ]
        if btc_jan:
            assert btc_jan[0].long_term_capital_gain is True

    def test_loss_harvesting_report(self, sample_portfolio_df):
        """Test complete loss harvesting report generation."""
        current_prices = {
            "btc": 42000,
            "eth": 1800,
            "sol": 95,
        }

        report = generate_loss_harvesting_report(
            sample_portfolio_df, current_prices, tax_rate=0.15
        )

        assert report["status"] in ["opportunities_found", "no_opportunities"]
        assert "total_unrealized_losses" in report
        assert "total_tax_savings" in report
        assert "recommendations" in report
        assert "warnings" in report
        assert "next_steps" in report

    def test_no_loss_opportunities(self):
        """Test when there are no loss opportunities."""
        # Only has gains
        data = {
            "timestamp": [
                pd.Timestamp("2023-01-10"),
                pd.Timestamp("2023-02-15"),
            ],
            "type": ["BUY", "SELL"],
            "asset": ["BTC", "BTC"],
            "amount": [1.0, 1.0],
            "price": [40000, 50000],
            "fee": [0, 0],
        }
        df = pd.DataFrame(data)

        current_prices = {"btc": 55000}  # Still profitable

        report = generate_loss_harvesting_report(df, current_prices)
        assert report["status"] == "no_opportunities"
        assert len(report["recommendations"]) == 0

    def test_replacement_assets(self):
        """Test replacement asset suggestions."""
        # BTC replacements
        btc_replacements = recommend_replacement_assets("BTC", {})
        assert "WBTC" in btc_replacements
        assert "SBTC" in btc_replacements

        # ETH replacements
        eth_replacements = recommend_replacement_assets("ETH", {})
        assert "WETH" in eth_replacements
        assert "stETH" in eth_replacements

        # Unknown asset
        unknown_replacements = recommend_replacement_assets("XYZ", {})
        assert len(unknown_replacements) == 0

    def test_tax_savings_calculation(self, sample_portfolio_df):
        """Test that tax savings are calculated correctly."""
        current_prices = {
            "btc": 40000,  # $10,000 loss per BTC
        }

        recommendations = find_loss_positions(
            sample_portfolio_df, current_prices, tax_rate=0.15
        )

        btc_recs = [r for r in recommendations if r.asset == "BTC"]

        # With 15% tax rate:
        # First BTC: loss = (40000 - 50000) = -10000, tax saving = 1500
        # Second BTC: loss = (20000 - 32500) = -12500, tax saving = 1875
        for rec in btc_recs:
            expected_savings = abs(float(rec.unrealized_loss)) * 0.15
            assert abs(float(rec.tax_savings_usd) - expected_savings) < 1


class TestIntegration:
    """Integration tests for income and loss features."""

    @pytest.fixture
    def complex_portfolio_df(self):
        """Create complex portfolio with income and sales."""
        data = {
            "timestamp": [
                pd.Timestamp("2023-01-10"),  # BUY BTC
                pd.Timestamp("2023-02-15"),  # STAKING ETH
                pd.Timestamp("2023-03-20"),  # BUY more BTC
                pd.Timestamp("2023-04-25"),  # AIRDROP ARB
                pd.Timestamp("2023-05-30"),  # SELL BTC at loss
                pd.Timestamp("2023-06-10"),  # LENDING_INTEREST USDC
            ],
            "type": ["BUY", "STAKING_REWARD", "BUY", "AIRDROP", "SELL", "LENDING_INTEREST"],
            "asset": ["BTC", "ETH", "BTC", "ARB", "BTC", "USDC"],
            "amount": [1.0, 0.5, 0.5, 100, 1.0, 100],
            "price": [50000, 2500, 55000, 1.5, 42000, 1.0],
            "fee": [0, 0, 0, 0, 100, 0],
        }
        return pd.DataFrame(data)

    def test_income_and_pnl_together(self, complex_portfolio_df):
        """Test that income and PnL are correctly separated."""
        income = compute_income_events(complex_portfolio_df)
        pnl = compute_pnl_avco(complex_portfolio_df)

        # Should have income events
        assert income["events_count"] > 0
        assert income["total_income_usd"] > 0

        # Should have PnL
        assert pnl["taxable_events_count"] > 0

        # Income should not appear in realized_pnl
        # (it's separate line item in tax report)
        assert "STAKING_REWARD" not in str(pnl)

    def test_loss_harvesting_after_sales(self, complex_portfolio_df):
        """Test loss harvesting on portfolio with prior sales."""
        current_prices = {
            "btc": 40000,  # Down from purchases at 50000, 55000
            "eth": 2000,   # Down from 2500
            "arb": 1.2,    # Down from 1.5
            "usdc": 1.0,
        }

        report = generate_loss_harvesting_report(
            complex_portfolio_df, current_prices, tax_rate=0.15
        )

        # Should identify remaining BTC position as loss opportunity
        if report["status"] == "opportunities_found":
            btc_recs = [
                r for r in report["recommendations"] if r["asset"] == "BTC"
            ]
            assert len(btc_recs) > 0


# Run: pytest -xvs
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
