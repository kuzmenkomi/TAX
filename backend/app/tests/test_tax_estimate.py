"""Tests for annual vs monthly tax estimation."""

import pytest

from app.accounting.tax_estimate import compute_tax_liability, uses_monthly_tax_settlement


class TestTaxEstimate:
    def test_us_offsets_losses_across_months(self):
        """March +10k, April -10k → zero annual tax (not $1,500)."""
        gains = {"2024-03": 10_000.0, "2024-04": 0.0}
        losses = {"2024-04": 10_000.0}
        total, monthly = compute_tax_liability(
            country="US",
            monthly_gains=gains,
            monthly_losses=losses,
            tax_year=2024,
        )
        assert total == pytest.approx(0.0)
        assert monthly == {}

    def test_us_tax_on_positive_annual_net(self):
        gains = {"2024-03": 20.28}
        total, _ = compute_tax_liability(
            country="US",
            monthly_gains=gains,
            monthly_losses={},
            tax_year=2024,
        )
        assert total == pytest.approx(3.042, rel=0.01)

    def test_brazil_uses_monthly_settlement(self):
        assert uses_monthly_tax_settlement("BR") is True
        assert uses_monthly_tax_settlement("US") is False

    def test_brazil_monthly_does_not_cross_offset(self):
        """Brazil: March profit taxed even if April wipes annual net (when threshold met)."""
        gains = {"2024-03": 10_000.0}
        losses = {"2024-04": 10_000.0}
        sales = {"2024-03": 40_000.0, "2024-04": 40_000.0}
        total, monthly = compute_tax_liability(
            country="BR",
            monthly_gains=gains,
            monthly_losses=losses,
            monthly_sales_brl=sales,
            tax_year=2024,
        )
        assert total == pytest.approx(1_500.0)
        assert monthly.get("2024-03") == pytest.approx(1_500.0)

    def test_brazil_below_threshold_no_tax(self):
        gains = {"2024-03": 10_000.0}
        sales = {"2024-03": 1_000.0}
        total, monthly = compute_tax_liability(
            country="BR",
            monthly_gains=gains,
            monthly_losses={},
            monthly_sales_brl=sales,
            tax_year=2024,
        )
        assert total == pytest.approx(0.0)
        assert monthly == {}
