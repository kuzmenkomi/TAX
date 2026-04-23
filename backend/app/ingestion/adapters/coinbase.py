from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter


class CoinbaseAdapter(BaseAdapter):
    """
    Minimal Coinbase CSV adapter.

    Supports common exports with columns like:
    - Timestamp / Transaction Date
    - Transaction Type / Type
    - Asset / Currency
    - Quantity Transacted / Amount
    - Fees and/or Total (if present)
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower().strip(): c for c in df.columns}

        def pick(*names: str) -> str | None:
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        ts_col = pick("timestamp", "transaction date", "date")
        type_col = pick("transaction type", "type")
        asset_col = pick("asset", "currency")
        qty_col = pick("quantity transacted", "quantity", "amount")
        fee_col = pick("fees", "fee")
        total_col = pick("total (inclusive of fees)", "total", "subtotal")
        id_col = pick("transaction id", "id")

        if not ts_col or not type_col or not asset_col or not qty_col:
            raise ValueError("Coinbase CSV: missing required columns (timestamp/type/asset/amount)")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")
        out["asset"] = df[asset_col].astype(str).str.strip().str.upper()
        out["amount"] = pd.to_numeric(df[qty_col], errors="coerce").abs()

        def map_type(v: Any) -> str:
            s = str(v).strip().lower()
            if "staking" in s or "reward" in s:
                return "STAKING"
            if "airdrop" in s:
                return "AIRDROP"
            if "interest" in s:
                return "INTEREST"
            if "buy" in s:
                return "BUY"
            if "sell" in s:
                return "SELL"
            if "receive" in s or "deposit" in s:
                return "RECEIVE"
            if "send" in s or "withdraw" in s:
                return "TRANSFER"
            return "OTHER"

        out["type"] = df[type_col].apply(map_type)
        out["fee"] = pd.to_numeric(df[fee_col], errors="coerce").fillna(0.0) if fee_col else 0.0
        out["from_wallet"] = "Coinbase"
        out["to_wallet"] = "Coinbase"
        out["network"] = "coinbase"
        out["fee_asset"] = out["asset"]
        out["external_id"] = df[id_col].astype(str) if id_col else ""

        if total_col:
            out["total_value"] = pd.to_numeric(df[total_col], errors="coerce")
        else:
            out["total_value"] = pd.NA
        out["price"] = pd.NA

        return out

