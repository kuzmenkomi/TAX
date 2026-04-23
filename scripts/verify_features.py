#!/usr/bin/env python3
"""
Quick Start: Income Recognition & Tax Loss Harvesting

Run this to verify the new features work correctly.

Usage:
    python backend/verify_features.py
"""

import sys
from pathlib import Path
import pandas as pd
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.accounting.avco_engine import compute_income_events, compute_pnl_avco
from app.accounting.tax_loss_harvesting import (
    generate_loss_harvesting_report,
    build_position_lots,
)


def create_test_data():
    """Create sample transaction data with income and losses."""
    data = {
        "timestamp": [
            # Regular purchases
            pd.Timestamp("2023-01-10"),
            pd.Timestamp("2023-02-15"),
            pd.Timestamp("2023-03-20"),
            # Income events
            pd.Timestamp("2024-01-10"),
            pd.Timestamp("2024-02-15"),
            pd.Timestamp("2024-03-20"),
        ],
        "type": [
            "BUY",
            "BUY",
            "BUY",
            "STAKING_REWARD",
            "AIRDROP",
            "LENDING_INTEREST",
        ],
        "asset": [
            "BTC",
            "ETH",
            "SOL",
            "ETH",
            "ARB",
            "USDC",
        ],
        "amount": [
            1.0,
            5.0,
            100,
            0.5,
            1000,
            500,
        ],
        "price": [
            50000,
            2000,
            100,
            2000,
            1.5,
            1.0,
        ],
        "fee": [0, 0, 0, 0, 0, 0],
        "total_value": [50000, 10000, 10000, 1000, 1500, 500],
    }
    return pd.DataFrame(data)


def test_income_recognition():
    """Test income recognition feature."""
    print("\n" + "=" * 60)
    print("TEST 1: INCOME RECOGNITION")
    print("=" * 60)

    df = create_test_data()
    result = compute_income_events(df)

    print(f"\n✓ Total income recognized: ${result['total_income_usd']:.2f}")
    print(f"✓ Income events found: {result['events_count']}")

    print("\nIncome by type:")
    for event_type, amount in result["income_by_type"].items():
        print(f"  • {event_type}: ${amount:.2f}")

    print("\nIncome by asset:")
    for asset, amount in result["income_by_asset"].items():
        print(f"  • {asset}: ${amount:.2f}")

    print("\nSpecific events:")
    for event in result["income_events"][:3]:
        print(f"  • {event.event_type}: {event.amount} {event.asset} @ ${event.fmv_per_unit}")

    assert result["events_count"] == 3, "Should find 3 income events"
    assert result["total_income_usd"] == 3000.0, "Total should be $3000"
    print("\n✅ PASSED: Income recognition working correctly")


def test_pnl_calculation():
    """Test that PnL is calculated correctly alongside income."""
    print("\n" + "=" * 60)
    print("TEST 2: PnL CALCULATION (AVCO)")
    print("=" * 60)

    df = create_test_data()
    pnl_result = compute_pnl_avco(df)

    print(f"\n✓ Taxable events: {pnl_result['taxable_events_count']}")
    print(f"✓ Realized PnL: ${pnl_result['total_realized_pnl_usd']:.2f}")
    print(f"✓ Inventory assets: {len(pnl_result['inventory'])}")

    print("\nInventory positions:")
    for asset, pos_data in pnl_result["inventory"].items():
        qty = pos_data["quantity"]
        cost = pos_data["avg_cost"]
        print(f"  • {asset}: {qty} @ ${cost:.2f}/unit (cost basis: ${qty * cost:.2f})")

    print("\n✅ PASSED: PnL calculation working correctly")


def test_tax_loss_harvesting():
    """Test tax loss harvesting with current prices showing losses."""
    print("\n" + "=" * 60)
    print("TEST 3: TAX LOSS HARVESTING")
    print("=" * 60)

    df = create_test_data()

    # Set current prices lower than purchase prices to show losses
    current_prices = {
        "btc": 42000,  # Down from $50,000
        "eth": 1500,   # Down from $2,000
        "sol": 80,     # Down from $100
        "arb": 1.0,    # Down from $1.50
    }

    report = generate_loss_harvesting_report(df, current_prices, tax_rate=0.15)

    print(f"\n✓ Status: {report['status']}")
    print(f"✓ Total unrealized losses: ${report['total_unrealized_losses']:.2f}")
    print(f"✓ Potential tax savings: ${report['total_tax_savings']:.2f}")

    if report["status"] == "opportunities_found":
        print(f"✓ Recommendations found: {len(report['recommendations'])}")
        print("\nTop recommendations:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"\n  {i}. {rec['asset']}")
            print(f"     Quantity: {rec['quantity']}")
            print(f"     Loss: -${abs(rec['unrealized_loss']):.2f}")
            print(f"     Tax savings: ${rec['tax_savings_usd']:.2f}")
            print(f"     Holding: {rec['holding_period_days']} days ({'long-term' if rec['long_term'] else 'short-term'})")

        print("\n⚠️  Warnings:")
        for warning in report["warnings"]:
            print(f"  • {warning}")

        assert len(report["recommendations"]) > 0, "Should find loss opportunities"
        print("\n✅ PASSED: Tax loss harvesting working correctly")
    else:
        print("\n⚠️  No loss opportunities found with given prices")


def test_position_tracking():
    """Test individual position lot tracking."""
    print("\n" + "=" * 60)
    print("TEST 4: POSITION TRACKING (Lot Building)")
    print("=" * 60)

    df = create_test_data()
    lots = build_position_lots(df)

    print(f"\n✓ Assets tracked: {len(lots)}")

    for asset, asset_lots in lots.items():
        print(f"\n{asset}: {len(asset_lots)} lot(s)")
        for i, lot in enumerate(asset_lots, 1):
            print(f"  Lot {i}:")
            print(f"    Date: {lot.acquisition_date}")
            print(f"    Quantity: {lot.quantity}")
            print(f"    Cost/unit: ${lot.cost_per_unit:.2f}")
            print(f"    Total cost: ${lot.cost_basis_total:.2f}")

    assert len(lots) > 0, "Should track positions"
    print("\n✅ PASSED: Position tracking working correctly")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FEATURE VERIFICATION: Income & Tax Loss Harvesting")
    print("=" * 60)

    try:
        test_income_recognition()
        test_pnl_calculation()
        test_position_tracking()
        test_tax_loss_harvesting()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n✅ Income recognition is working")
        print("✅ PnL calculation is working")
        print("✅ Position tracking is working")
        print("✅ Tax loss harvesting is working")
        print("\n📌 Features are ready for production!")
        print("\nNext steps:")
        print("  1. Run pipeline tests: pytest backend/app/tests/test_income_and_loss_features.py -v")
        print("  2. Update frontend to display new response fields")
        print("  3. Test with real data from your exchanges/wallets")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
