"""Open-position inventory using the same accounting method as tax analysis."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

import pandas as pd

from app.accounting.avco_engine import _buy_acquisition, _d, compute_pnl_avco
from app.accounting.calculator import Lot, _consume_lots

_INCOME_AND_ADDITIONS = frozenset(
    {
        "BUY",
        "IN",
        "RECEIVE",
        "DEPOSIT",
        "STAKING_REWARD",
        "AIRDROP",
        "LENDING_INTEREST",
        "MINING",
        "FARMING_REWARD",
        "INTEREST",
        "STAKING",
        "LENDING",
    }
)
_SELL_TYPES = frozenset({"SELL", "OUT", "WITHDRAW"})


def _timestamp_seconds(value: Any) -> int:
    if value is None:
        return 0
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return 0
    if pd.isna(ts):
        return 0
    return int(ts.timestamp())


def compute_open_inventory(df: pd.DataFrame, accounting_method: str = "AVCO") -> dict[str, dict[str, float]]:
    """
    Remaining holdings after processing all transactions in chronological order.

    Returns {ASSET: {"quantity": float, "avg_cost": float}} compatible with AVCO output.
    """
    method = (accounting_method or "AVCO").upper()
    if method == "AVCO":
        return compute_pnl_avco(df).get("inventory", {})

    inventory: dict[str, deque[Lot]] = defaultdict(deque)
    if df.empty:
        return {}

    for _, tx in df.sort_values("timestamp").iterrows():
        tx_type = str(tx.get("type", "")).upper()
        asset = str(tx.get("asset", "")).upper()
        amount = _d(tx.get("amount"))
        price = _d(tx.get("price"))
        fee = _d(tx.get("fee"))

        if not asset or asset == "SWAP":
            continue

        if tx_type in _INCOME_AND_ADDITIONS:
            if amount <= 0:
                continue
            net_amount, total_cost = _buy_acquisition(tx, asset, amount, price)
            if net_amount <= 0 or total_cost <= 0:
                continue
            unit_cost = total_cost / net_amount
            inventory[asset].append(
                Lot(
                    quantity=float(net_amount),
                    unit_cost=float(unit_cost),
                    timestamp=_timestamp_seconds(tx.get("timestamp")),
                )
            )
        elif tx_type in _SELL_TYPES:
            if amount <= 0:
                continue
            lots = inventory[asset]
            if not lots:
                continue
            try:
                _consume_lots(method, lots, float(amount))
            except ValueError:
                continue
        elif tx_type == "TRANSFER" and fee > 0:
            fee_asset = str(tx.get("fee_asset", asset)).upper() or asset
            lots = inventory[fee_asset]
            if not lots:
                continue
            try:
                _consume_lots(method, lots, float(fee))
            except ValueError:
                continue

    result: dict[str, dict[str, float]] = {}
    for asset, lots in inventory.items():
        quantity = sum(lot.quantity for lot in lots)
        if quantity <= 0:
            continue
        cost_basis = sum(lot.quantity * lot.unit_cost for lot in lots)
        result[asset] = {
            "quantity": float(quantity),
            "avg_cost": float(cost_basis / quantity),
        }
    return result
