from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter


class BybitAdapter(BaseAdapter):
    """
    Minimal Bybit CSV adapter.

    Bybit exports vary (Spot/Derivatives/Funding). This adapter targets simple
    wallet/asset movement history with columns like:
    - Time / Date
    - Type / Transaction Type
    - Coin / Currency
    - Amount
    - Fee (optional)
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower().strip(): c for c in df.columns}

        def pick(*names: str) -> str | None:
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        ts_col = pick("time", "date", "timestamp")
        type_col = pick("type", "transaction type")
        asset_col = pick("coin", "currency", "asset")
        amount_col = pick("amount", "change")
        fee_col = pick("fee", "tx fee", "commission")
        id_col = pick("txid", "transaction id", "id")

        if not ts_col or not type_col or not asset_col or not amount_col:
            raise ValueError("Bybit CSV: missing required columns (time/type/coin/amount)")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")
        out["asset"] = df[asset_col].astype(str).str.strip().str.upper()
        out["amount"] = pd.to_numeric(df[amount_col], errors="coerce").abs()

        def map_type(v: Any) -> str:
            s = str(v).strip().lower()
            if "staking" in s or "reward" in s:
                return "STAKING"
            if "airdrop" in s:
                return "AIRDROP"
            if "interest" in s or "earn" in s:
                return "INTEREST"
            if "lending" in s:
                return "LENDING"
            if "deposit" in s or "receive" in s:
                return "RECEIVE"
            if "withdraw" in s or "send" in s:
                return "TRANSFER"
            if "buy" in s:
                return "BUY"
            if "sell" in s:
                return "SELL"
            return "OTHER"

        out["type"] = df[type_col].apply(map_type)
        out["fee"] = pd.to_numeric(df[fee_col], errors="coerce").fillna(0.0) if fee_col else 0.0
        out["from_wallet"] = "Bybit"
        out["to_wallet"] = "Bybit"
        out["network"] = "bybit"
        out["fee_asset"] = out["asset"]
        out["external_id"] = df[id_col].astype(str) if id_col else ""
        out["price"] = pd.NA
        out["total_value"] = pd.NA
        return out

