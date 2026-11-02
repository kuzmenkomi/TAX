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


_QUOTE_FEE_ASSETS = frozenset(
    {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "EUR", "GBP", "BRL", "PYUSD"}
)


def _resolve_fee_asset(tx: pd.Series, asset: str, amount: Decimal) -> str:
    explicit = str(tx.get("fee_asset") or "").strip().upper()
    if explicit:
        return explicit
    fee = _d(tx.get("fee"))
    if fee <= 0:
        return ""
    # Binance-style exports often omit fee_asset; a fee larger than the traded
    # quantity is denominated in quote currency (e.g. USDT), not the base asset.
    if fee >= amount:
        return "USDT"
    return asset


def _quote_fee_usd(fee: Decimal, fee_asset: str) -> Decimal:
    if fee <= 0:
        return Decimal("0")
    if fee_asset in _QUOTE_FEE_ASSETS:
        return fee
    return Decimal("0")


def _buy_acquisition(tx: pd.Series, asset: str, amount: Decimal, price: Decimal) -> tuple[Decimal, Decimal]:
    """Return (net_quantity_added, total_cost_usd) for a BUY/IN/RECEIVE row."""
    fee = _d(tx.get("fee"))
    fee_asset = _resolve_fee_asset(tx, asset, amount)
    fee_in_acquired_asset = fee > 0 and fee_asset == asset and fee < amount
    net_amount = amount - fee if fee_in_acquired_asset else amount
    if net_amount <= 0:
        return Decimal("0"), Decimal("0")

    total_value = _d(tx.get("total_value"))
    if total_value > 0:
        total_cost = total_value + _quote_fee_usd(fee, fee_asset)
        return net_amount, total_cost

    fee_value = Decimal("0")
    if fee > 0 and not fee_in_acquired_asset:
        quote_fee = _quote_fee_usd(fee, fee_asset)
        fee_value = quote_fee if quote_fee > 0 else fee * price
    return net_amount, amount * price + fee_value


def _sell_proceeds(tx: pd.Series, asset: str, amount: Decimal, price: Decimal) -> Decimal:
    fee = _d(tx.get("fee"))
    fee_asset = _resolve_fee_asset(tx, asset, amount)
    total_value = _d(tx.get("total_value"))

    if total_value > 0:
        return total_value - _quote_fee_usd(fee, fee_asset)

    fee_value = Decimal("0")
    if fee > 0:
        quote_fee = _quote_fee_usd(fee, fee_asset)
        fee_value = quote_fee if quote_fee > 0 else fee * price
    return amount * price - fee_value


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
    """

    inventory: DefaultDict[str, AvcoPosition] = defaultdict(AvcoPosition)
    realized: DefaultDict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    lot_matches: list[dict[str, Any]] = []
    taxable_events = 0
    total_gas_fees = Decimal("0")

    df_sorted = df.sort_values("timestamp").copy()

    income_and_additions = {
        "BUY", "IN", "RECEIVE", "DEPOSIT",
        "STAKING_REWARD", "AIRDROP", "LENDING_INTEREST", "MINING", "FARMING_REWARD",
        "INTEREST", "STAKING", "LENDING",
    }

    for _, tx in df_sorted.iterrows():
        t = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        amount = _d(tx.get("amount"))
        price = _d(tx.get("price"))
        fee = _d(tx.get("fee"))
        timestamp = tx.get("timestamp")
        ext_id = tx.get("id", tx.get("external_id", ""))

        if asset in ("", "SWAP"):
            continue

        if t in income_and_additions:
            if amount <= 0:
                continue
            # Cost basis computation:
            # 1. If exchange-provided total_value exists → use it directly (no fee inflation)
            # 2. Otherwise: amount * price + fee * price (legacy Binance-style heuristic)
            total_value = _d(tx.get("total_value"))
            if total_value > 0:
                total_cost = total_value
            else:
                fee_value = fee * price if fee > 0 else Decimal("0")
                total_cost = amount * price + fee_value
            if total_cost <= 0:
                continue
            pos = inventory[asset]
            new_qty = pos.quantity + amount
            if new_qty > 0:
                pos.avg_cost = (pos.quantity * pos.avg_cost + total_cost) / new_qty
            pos.quantity = new_qty

        elif t in ("SELL", "OUT", "WITHDRAW"):
            if amount <= 0:
                continue
            pos = inventory[asset]
            if pos.quantity <= 0:
                continue
            
            proceeds = _sell_proceeds(tx, asset, amount, price)
            cost_basis = amount * pos.avg_cost
            gain_loss = proceeds - cost_basis
            
            realized[asset] += gain_loss
            pos.quantity -= amount
            taxable_events += 1
            
            sell_ts = timestamp
            lot_matches.append({
                "asset": asset,
                "amount": float(amount),
                "buy_price": float(pos.avg_cost),  # average cost as buy_price
                "sell_price": float(price) if price > 0 else (float(proceeds / amount) if amount > 0 else 0.0),
                "cost_basis": float(cost_basis),
                "proceeds": float(proceeds),
                "gain_loss": float(gain_loss),
                "buy_timestamp": sell_ts,   # AVCO has no single buy; use sell_ts as placeholder
                "sell_timestamp": sell_ts,
                "sell_tx_id": None,         # resolved later after DB insert
                "sell_tx_external_id": str(tx.get("external_id") or ext_id or ""),
                "buy_tx_id": None,
                "buy_tx_external_id": "",
            })

        elif t == "TRANSFER":
            if fee > 0:
                fee_asset = str(tx.get("fee_asset", asset)).upper() or asset
                fee_price = price
                fee_usd = fee * fee_price
                total_gas_fees += fee_usd
                realized["GAS_EXPENSE"] -= fee_usd
                taxable_events += 1
                pos = inventory[fee_asset]
                pos.quantity -= fee

    total_realized = sum(realized.values())

    return {
        "total_realized_pnl_usd": float(total_realized),
        "realized_pnl_by_asset": {k: float(v) for k, v in realized.items()},
        "lot_matches": lot_matches,
        "taxable_events_count": int(taxable_events),
        "internal_transfer_count": 0,
        "total_gas_fees_usd": float(total_gas_fees),
        "engine": "avco",
        "inventory": {k: {"quantity": float(v.quantity), "avg_cost": float(v.avg_cost)} for k, v in inventory.items() if v.quantity > 0},
    }


def compute_positions_with_unrealized_pnl(
    df: pd.DataFrame,
    current_prices: dict[str, float],
    accounting_method: str = "AVCO",
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
    
    from app.accounting.inventory_engine import compute_open_inventory

    inventory = compute_open_inventory(df, accounting_method)
    
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

