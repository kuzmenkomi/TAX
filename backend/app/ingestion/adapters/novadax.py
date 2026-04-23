from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter


class NovaDaxAdapter(BaseAdapter):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower().strip(): c for c in df.columns}

        def pick(*names: str) -> str | None:
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        ts_col = pick("created_at", "date", "timestamp", "data")
        type_col = pick("type", "side", "operation", "tipo")
        asset_col = pick("symbol", "asset", "coin", "ativo")
        amount_col = pick("amount", "quantity", "quantidade")
        fee_col = pick("fee", "taxa", "commission")
        price_col = pick("price", "preco")
        id_col = pick("id", "order_id", "trade_id")
        if not ts_col or not type_col or not asset_col or not amount_col:
            raise ValueError("NovaDAX CSV: required columns missing.")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")
        out["asset"] = df[asset_col].astype(str).str.replace("/BRL", "", regex=False).str.upper()
        out["amount"] = pd.to_numeric(df[amount_col], errors="coerce").abs()

        def map_type(v: Any) -> str:
            s = str(v).strip().lower()
            if "buy" in s or "compra" in s:
                return "BUY"
            if "sell" in s or "venda" in s:
                return "SELL"
            if "deposit" in s:
                return "RECEIVE"
            if "withdraw" in s or "saque" in s:
                return "TRANSFER"
            return "TRANSFER"

        out["type"] = df[type_col].apply(map_type)
        out["fee"] = pd.to_numeric(df[fee_col], errors="coerce").fillna(0.0) if fee_col else 0.0
        out["from_wallet"] = "NovaDAX"
        out["to_wallet"] = "NovaDAX"
        out["network"] = "novadax"
        out["fee_asset"] = out["asset"]
        out["external_id"] = df[id_col].astype(str) if id_col else ""
        out["price"] = pd.to_numeric(df[price_col], errors="coerce") if price_col else pd.NA
        out["total_value"] = pd.NA
        return out
