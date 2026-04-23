from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import Any, DefaultDict
from collections import defaultdict

import pandas as pd


getcontext().prec = 28


@dataclass
class AvcoPosition:
    quantity: Decimal = Decimal("0")
    avg_cost: Decimal = Decimal("0")  # USD per unit


@dataclass
class IncomeEvent:
    """Taxable income recognition event (staking, airdrop, etc.)."""
    timestamp: pd.Timestamp
    event_type: str  # STAKING_REWARD, AIRDROP, LENDING_INTEREST, MINING, FARMING_REWARD
    asset: str
    amount: Decimal  # quantity received
    fmv_per_unit: Decimal  # Fair Market Value in USD per unit at receipt
    total_usd: Decimal  # total FMV = amount * fmv_per_unit
    note: str = ""


def _d(x: Any) -> Decimal:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return Decimal("0")
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")


def compute_income_events(df: pd.DataFrame) -> dict[str, Any]:
    """
    Extract income recognition events (STAKING, AIRDROP, LENDING, MINING, etc.).

    These are taxable income events that must be recognized at Fair Market Value (FMV)
    on the date of receipt. They are separate from capital gains/losses.

    Income types recognized:
    - STAKING_REWARD: Proof-of-Stake rewards
    - AIRDROP: Token distributions
    - LENDING_INTEREST: Yield from lending protocols
    - MINING: Mining rewards (Proof-of-Work)
    - FARMING_REWARD: DeFi farming/yield farming rewards
    - INTEREST: Generic interest payments

    Args:
        df: Normalized transaction dataframe

    Returns:
        Dict containing:
        - income_events: List of IncomeEvent objects
        - total_income_usd: Total taxable income in USD
        - income_by_type: Breakdown by type
        - income_by_asset: Breakdown by asset
    """
    income_events: list[IncomeEvent] = []
    df_sorted = df.sort_values("timestamp").copy()

    # Income transaction types
    income_types = {
        "STAKING_REWARD",  # Proof-of-Stake rewards
        "AIRDROP",         # Token distributions
        "LENDING_INTEREST",  # Lending protocol yields
        "MINING",          # Mining rewards
        "FARMING_REWARD",  # DeFi farming rewards
        "INTEREST",        # Generic interest
        "STAKING",         # Alias for STAKING_REWARD
        "LENDING",         # Alias for LENDING_INTEREST
    }

    for _, tx in df_sorted.iterrows():
        t = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        amount = _d(tx.get("amount"))
        price = _d(tx.get("price"))
        timestamp = tx.get("timestamp")

        # Skip invalid rows
        if asset in ("", "SWAP") or amount <= 0 or price <= 0:
            continue

        # Check if this is an income type
        if t not in income_types:
            continue

        # Normalize type name
        event_type = t
        if t == "STAKING":
            event_type = "STAKING_REWARD"
        elif t == "LENDING":
            event_type = "LENDING_INTEREST"

        total_usd = amount * price

        event = IncomeEvent(
            timestamp=timestamp,
            event_type=event_type,
            asset=asset,
            amount=amount,
            fmv_per_unit=price,
            total_usd=total_usd,
            note=tx.get("note", ""),
        )
        income_events.append(event)

    # Aggregate statistics
    total_income = sum(e.total_usd for e in income_events)

    income_by_type: DefaultDict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for event in income_events:
        income_by_type[event.event_type] += event.total_usd

    income_by_asset: DefaultDict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for event in income_events:
        income_by_asset[event.asset] += event.total_usd

    return {
        "income_events": income_events,
        "total_income_usd": float(total_income),
        "income_by_type": {k: float(v) for k, v in income_by_type.items()},
        "income_by_asset": {k: float(v) for k, v in income_by_asset.items()},
        "events_count": len(income_events),
    }


def compute_pnl_avco(df: pd.DataFrame) -> dict[str, Any]:
    """
    Average cost accounting (AVCO).

    Assumptions for MVP:
    - Uses df columns from normalizer: timestamp, type, asset, amount, fee, price, total_value.
    - BUY/RECEIVE/IN/STAKING/AIRDROP/LENDING/MINING increase inventory at spot price.
    - SELL/OUT decrease inventory and realize PnL using average cost.
    - TRANSFER is not taxable except fee: we model fee as disposal at spot price of fee_asset (simplified).
    
    Important: Income types (STAKING, AIRDROP, LENDING, MINING) are recognized as:
    1. Inventory addition at FMV (for cost basis tracking)
    2. Separate income events (for tax reporting as "income" not capital gains)
    
    The compute_income_events() function should be called separately to extract income events.
    """

    inventory: DefaultDict[str, AvcoPosition] = defaultdict(AvcoPosition)
    realized: DefaultDict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    taxable_events = 0
    total_gas_fees = Decimal("0")

    df_sorted = df.sort_values("timestamp").copy()

    # Income types that should be recognized as income but also added to inventory
    income_and_additions = {
        "BUY", "IN", "RECEIVE", "DEPOSIT",  # Regular purchases/deposits
        "STAKING_REWARD", "AIRDROP", "LENDING_INTEREST", "MINING", "FARMING_REWARD",  # Income events
        "INTEREST", "STAKING", "LENDING",  # Aliases
    }

    for _, tx in df_sorted.iterrows():
        t = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        amount = _d(tx.get("amount"))
        price = _d(tx.get("price"))
        fee = _d(tx.get("fee"))

        if asset in ("", "SWAP"):
            continue

        if t in income_and_additions:
            # Acquire at price (USD per unit)
            # This applies to both regular purchases and income events
            # Income events are recorded at FMV on receipt date (which is the price)
            if amount <= 0:
                continue
            fee_value = fee * price if fee > 0 else Decimal("0")
            total_cost = amount * price + fee_value
            pos = inventory[asset]
            new_qty = pos.quantity + amount
            if new_qty > 0:
                pos.avg_cost = (pos.quantity * pos.avg_cost + total_cost) / new_qty
            pos.quantity = new_qty

        elif t in ("SELL", "OUT", "WITHDRAW"):
            if amount <= 0:
                continue
            pos = inventory[asset]
            fee_value = fee * price if fee > 0 else Decimal("0")
            proceeds = amount * price - fee_value
            cost_basis = amount * pos.avg_cost
            realized[asset] += proceeds - cost_basis
            pos.quantity -= amount
            taxable_events += 1

        elif t == "TRANSFER":
            # Not taxable transfer itself, but fee is a taxable disposal (simplified, fee_asset == asset)
            if fee > 0:
                fee_asset = str(tx.get("fee_asset", asset)).upper() or asset
                fee_price = price  # best-effort
                fee_usd = fee * fee_price
                total_gas_fees += fee_usd
                realized["GAS_EXPENSE"] -= fee_usd
                taxable_events += 1
                # reduce inventory of fee asset by fee at avg cost (if exists)
                pos = inventory[fee_asset]
                pos.quantity -= fee

    total_realized = sum(realized.values())

    return {
        "total_realized_pnl_usd": float(total_realized),
        "realized_pnl_by_asset": {k: float(v) for k, v in realized.items()},
        "taxable_events_count": int(taxable_events),
        "internal_transfer_count": 0,
        "total_gas_fees_usd": float(total_gas_fees),
        "engine": "avco",
        "inventory": {k: {"quantity": float(v.quantity), "avg_cost": float(v.avg_cost)} for k, v in inventory.items() if v.quantity > 0},
    }


def compute_positions_with_unrealized_pnl(
    df: pd.DataFrame, current_prices: dict[str, float]
) -> list[dict[str, Any]]:
    """
    Compute current open positions with unrealized PnL.
    
    Args:
        df: Normalized transaction dataframe
        current_prices: Dict mapping asset symbol to current price in USD
        
    Returns:
        List of dicts with:
        - asset: symbol (e.g., "BTC")
        - quantity: open position quantity
        - avg_cost_usd: average cost per unit in USD
        - current_price_usd: current price per unit in USD
        - cost_basis_usd: total cost for this position
        - current_value_usd: total value at current price
        - unrealized_pnl_usd: unrealized gain/loss in USD
        - unrealized_pnl_pct: unrealized percentage
    """
    result = []
    
    # Get inventory first
    pnl_result = compute_pnl_avco(df)
    inventory = pnl_result.get("inventory", {})
    
    for asset, pos_data in inventory.items():
        quantity = Decimal(str(pos_data["quantity"]))
        avg_cost = Decimal(str(pos_data["avg_cost"]))
        
        if quantity <= 0:
            continue
            
        current_price = Decimal(str(current_prices.get(asset.lower(), 0)))
        if current_price <= 0:
            # Skip positions without current price
            continue
            
        cost_basis = quantity * avg_cost
        current_value = quantity * current_price
        unrealized_pnl = current_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else Decimal("0")
        
        result.append({
            "asset": asset,
            "quantity": float(quantity),
            "avg_cost_usd": float(avg_cost),
            "current_price_usd": float(current_price),
            "cost_basis_usd": float(cost_basis),
            "current_value_usd": float(current_value),
            "unrealized_pnl_usd": float(unrealized_pnl),
            "unrealized_pnl_pct": float(unrealized_pnl_pct),
        })
    
    # Sort by current value descending
    result.sort(key=lambda x: x["current_value_usd"], reverse=True)
    return result

