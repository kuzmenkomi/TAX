"""
Tax Loss Harvesting Engine.

Identifies positions with unrealized losses and recommends specific lots for sale
to minimize tax liability while maintaining portfolio exposure.

Features:
- Real-time loss calculation per position
- Specific lot recommendations
- Tax savings estimation
- Wash sale rule checking (future)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

import pandas as pd


@dataclass
class TaxPosition:
    """Single tax lot (cost basis batch)."""
    asset: str
    quantity: Decimal
    cost_per_unit: Decimal  # USD
    acquisition_date: pd.Timestamp
    cost_basis_total: Decimal  # quantity * cost_per_unit

    @property
    def current_value(self, current_price: Decimal) -> Decimal:
        """Current value at given price."""
        return self.quantity * current_price

    @property
    def unrealized_loss(self, current_price: Decimal) -> Decimal:
        """Unrealized loss (negative = loss)."""
        current_value = self.quantity * current_price
        return current_value - self.cost_basis_total

    def tax_savings(self, unrealized_loss: Decimal, tax_rate: Decimal = Decimal("0.15")) -> Decimal:
        """Tax savings if sold now."""
        if unrealized_loss >= 0:
            return Decimal("0")
        return abs(unrealized_loss) * tax_rate


@dataclass
class HarvestingRecommendation:
    """Tax loss harvesting recommendation."""
    asset: str
    lot_quantity: Decimal
    cost_per_unit: Decimal
    current_price: Decimal
    unrealized_loss: Decimal
    tax_savings_usd: Decimal
    acquisition_date: pd.Timestamp
    holding_period_days: int
    long_term_capital_gain: bool  # > 1 year
    reason: str
    action: str  # "SELL_NOW" or "MONITOR"


def build_position_lots(df: pd.DataFrame) -> dict[str, list[TaxPosition]]:
    """
    Build list of tax lots by tracking cost basis acquisitions.

    Groups all BUY/RECEIVE/DEPOSIT/STAKING/INTEREST transactions as separate lots.

    Returns:
        Dict: {asset: [list of TaxPosition]}
    """
    lots: dict[str, list[TaxPosition]] = defaultdict(list)

    df_sorted = df.sort_values("timestamp").copy()

    for _, tx in df_sorted.iterrows():
        tx_type = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        amount = float(tx.get("amount", 0) or 0)
        price = float(tx.get("price", 0) or 0)
        timestamp = tx.get("timestamp")
        fee = float(tx.get("fee", 0) or 0)

        # Skip invalid data
        if not asset or asset == "" or amount <= 0 or price <= 0:
            continue

        # These transaction types create new cost basis lots
        if tx_type in ("BUY", "IN", "RECEIVE", "DEPOSIT", "STAKING", "INTEREST", "AIRDROP",
                       "MINING", "LENDING", "FARMING_REWARD"):

            # Include fee in cost basis
            fee_value = (fee * price) if fee > 0 else 0.0
            total_cost = (amount * price) + fee_value
            cost_per_unit = total_cost / amount if amount > 0 else 0.0

            lot = TaxPosition(
                asset=asset,
                quantity=Decimal(str(amount)),
                cost_per_unit=Decimal(str(cost_per_unit)),
                acquisition_date=timestamp,
                cost_basis_total=Decimal(str(total_cost)),
            )
            lots[asset].append(lot)

        # SELL/OUT/WITHDRAW removes from lots (FIFO or specific)
        elif tx_type in ("SELL", "OUT", "WITHDRAW"):
            if asset in lots and lots[asset]:
                remaining = float(amount)
                # Remove lots in FIFO order (oldest first)
                while remaining > 0 and lots[asset]:
                    lot = lots[asset][0]
                    if lot.quantity <= Decimal(str(remaining)):
                        # Entire lot sold
                        remaining -= float(lot.quantity)
                        lots[asset].pop(0)
                    else:
                        # Partial lot sold
                        lot.quantity -= Decimal(str(remaining))
                        remaining = 0

    # Clean up empty lots
    for asset in list(lots.keys()):
        lots[asset] = [lot for lot in lots[asset] if lot.quantity > 0]
        if not lots[asset]:
            del lots[asset]

    return lots


def find_loss_positions(
    df: pd.DataFrame,
    current_prices: dict[str, float],
    tax_rate: float = 0.15,
    min_loss_usd: float = 100.0,
) -> list[HarvestingRecommendation]:
    """
    Find all positions with unrealized losses and recommend specific loss harvesting.

    Args:
        df: Normalized transaction DataFrame
        current_prices: Dict of {asset: current_price_usd}
        tax_rate: Marginal tax rate (0.15 = 15%)
        min_loss_usd: Minimum loss to recommend (skip small losses)

    Returns:
        List of HarvestingRecommendation sorted by tax savings (largest first)
    """
    recommendations = []

    lots = build_position_lots(df)
    today = pd.Timestamp.now()

    for asset, asset_lots in sorted(lots.items()):
        current_price = Decimal(str(current_prices.get(asset.lower(), 0) or 0))

        if current_price <= 0:
            # No price data available
            continue

        for lot in asset_lots:
            current_value = lot.quantity * current_price
            unrealized_loss = current_value - lot.cost_basis_total

            # Only recommend if there's a loss
            if unrealized_loss >= 0:
                continue

            # Skip if too small
            if abs(float(unrealized_loss)) < min_loss_usd:
                continue

            tax_savings = abs(unrealized_loss) * Decimal(str(tax_rate))
            holding_period_days = (today - lot.acquisition_date).days

            # Check if long-term capital gain (>365 days)
            long_term = holding_period_days > 365

            reason = ""
            if long_term:
                reason = "Long-term capital loss (>1 year) - preferential tax treatment"
            else:
                reason = f"Short-term capital loss ({holding_period_days} days)"

            rec = HarvestingRecommendation(
                asset=asset,
                lot_quantity=lot.quantity,
                cost_per_unit=lot.cost_per_unit,
                current_price=current_price,
                unrealized_loss=unrealized_loss,
                tax_savings_usd=tax_savings,
                acquisition_date=lot.acquisition_date,
                holding_period_days=holding_period_days,
                long_term_capital_gain=long_term,
                reason=reason,
                action="SELL_NOW" if abs(float(unrealized_loss)) > 500 else "MONITOR",
            )
            recommendations.append(rec)

    # Sort by tax savings (largest first)
    recommendations.sort(key=lambda r: float(r.tax_savings_usd), reverse=True)

    return recommendations


def generate_loss_harvesting_report(
    df: pd.DataFrame,
    current_prices: dict[str, float],
    tax_rate: float = 0.15,
) -> dict[str, Any]:
    """
    Generate comprehensive tax loss harvesting report.

    Returns:
        Dict with recommendations, summary stats, and warnings
    """
    recommendations = find_loss_positions(df, current_prices, tax_rate)

    if not recommendations:
        return {
            "status": "no_opportunities",
            "message": "No tax loss harvesting opportunities found",
            "total_unrealized_losses": 0.0,
            "total_tax_savings": 0.0,
            "recommendations": [],
            "summary": {
                "assets_with_losses": 0,
                "total_positions_analyzed": 0,
                "long_term_losses_count": 0,
                "short_term_losses_count": 0,
            },
            "warnings": [],
        }

    # Summary statistics
    total_loss = sum(float(r.unrealized_loss) for r in recommendations)
    total_tax_savings = sum(float(r.tax_savings_usd) for r in recommendations)
    assets_with_losses = len(set(r.asset for r in recommendations))
    long_term_count = sum(1 for r in recommendations if r.long_term_capital_gain)
    short_term_count = len(recommendations) - long_term_count

    # Convert to JSON-serializable format
    recommendations_json = [
        {
            "asset": r.asset,
            "quantity": float(r.lot_quantity),
            "cost_per_unit": float(r.cost_per_unit),
            "current_price": float(r.current_price),
            "unrealized_loss": float(r.unrealized_loss),
            "tax_savings_usd": float(r.tax_savings_usd),
            "acquisition_date": r.acquisition_date.isoformat(),
            "holding_period_days": r.holding_period_days,
            "long_term": r.long_term_capital_gain,
            "reason": r.reason,
            "action": r.action,
        }
        for r in recommendations[:10]  # Top 10
    ]

    # Warnings
    warnings = []
    if short_term_count > long_term_count:
        warnings.append(
            f"Most losses are short-term ({short_term_count}). "
            "Consider holding until >1 year for preferential treatment."
        )

    if total_loss < -10000:
        warnings.append(
            f"Large unrealized losses detected ({abs(total_loss):,.2f} USD). "
            "Consider professional tax consultation before harvesting."
        )

    # Check for potential wash sale issues
    potential_wash_sales = _check_potential_wash_sales(df)
    if potential_wash_sales:
        warnings.append(
            f"Potential wash sale risk detected: {len(potential_wash_sales)} assets "
            "may trigger wash sale rules if reacquired within 30 days."
        )

    return {
        "status": "opportunities_found",
        "message": f"Found {len(recommendations)} tax loss harvesting opportunities",
        "total_unrealized_losses": abs(total_loss),
        "total_tax_savings": total_tax_savings,
        "recommendations": recommendations_json,
        "summary": {
            "assets_with_losses": assets_with_losses,
            "total_positions_analyzed": len(recommendations),
            "long_term_losses_count": long_term_count,
            "short_term_losses_count": short_term_count,
            "tax_rate_assumed": tax_rate,
        },
        "warnings": warnings,
        "next_steps": [
            "Review recommendations above",
            "Consider portfolio impact of selling",
            "Check for wash sale rule implications",
            "Execute sales before end of tax year",
            "Reinvest in similar (but not identical) assets",
        ],
    }


def _check_potential_wash_sales(df: pd.DataFrame) -> list[str]:
    """
    Simple wash sale check: if asset was sold at loss, check next 30 days for repurchase.

    Returns:
        List of assets with potential wash sale issues
    """
    issues = []

    df_sorted = df.sort_values("timestamp").copy()
    sales = {}  # asset -> sale_date with loss

    for _, tx in df_sorted.iterrows():
        tx_type = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        timestamp = tx.get("timestamp")

        if tx_type in ("SELL", "OUT", "WITHDRAW"):
            # Simplified: mark as loss if fee > 0 (proxy for loss)
            fee = float(tx.get("fee", 0) or 0)
            if fee > 0:
                sales[asset] = timestamp

        elif tx_type in ("BUY", "IN", "RECEIVE") and asset in sales:
            # Check if within 30 days of loss
            days_diff = (timestamp - sales[asset]).days
            if 0 < days_diff <= 30:
                issues.append(f"{asset} (reacquired {days_diff} days after loss)")

    return issues


def recommend_replacement_assets(
    asset: str,
    current_prices: dict[str, float],
) -> list[str]:
    """
    Suggest similar assets for reinvestment (avoiding wash sale).

    These have similar characteristics but are technically different securities.
    """
    # Asset mapping for similar replacements
    replacements = {
        "BTC": ["WBTC", "SBTC", "tBTC"],  # BTC proxies
        "ETH": ["WETH", "stETH", "rETH"],  # ETH staking variants
        "USDC": ["USDT", "BUSD", "DAI"],  # Stablecoin alternatives
        "USDT": ["USDC", "BUSD", "TUSD"],  # Stablecoin alternatives
        "SOL": ["mSOL", "sSOL", "LST"],  # SOL staking variants
    }

    return replacements.get(asset.upper(), [])
