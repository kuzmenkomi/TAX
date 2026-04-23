from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseAdapter


class MercadoBitcoinAdapter(BaseAdapter):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower().strip(): c for c in df.columns}

        def pick(*names: str) -> str | None:
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        ts_col = pick("data", "date", "timestamp", "created at")
        type_col = pick("tipo", "type", "operation", "side")
        asset_col = pick("ativo", "asset", "coin", "symbol")
        amount_col = pick("quantidade", "amount", "quantity", "volume")
        fee_col = pick("taxa", "fee", "commission")
        price_col = pick("preco", "price")
        id_col = pick("id", "external_id", "trade id")
        if not ts_col or not type_col or not asset_col or not amount_col:
            raise ValueError("Mercado Bitcoin CSV: required columns missing.")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")
        out["asset"] = df[asset_col].astype(str).str.replace("/BRL", "", regex=False).str.upper()
        out["amount"] = pd.to_numeric(df[amount_col], errors="coerce").abs()

        def map_type(v: Any) -> str:
            s = str(v).strip().lower()
            if "compra" in s or "buy" in s:
                return "BUY"
            if "venda" in s or "sell" in s:
                return "SELL"
            if "saque" in s or "withdraw" in s:
                return "TRANSFER"
            if "deposit" in s:
                return "RECEIVE"
            return "TRANSFER"

        out["type"] = df[type_col].apply(map_type)
        out["fee"] = pd.to_numeric(df[fee_col], errors="coerce").fillna(0.0) if fee_col else 0.0
        out["from_wallet"] = "MercadoBitcoin"
        out["to_wallet"] = "MercadoBitcoin"
        out["network"] = "mercado_bitcoin"
        out["fee_asset"] = out["asset"]
        out["external_id"] = df[id_col].astype(str) if id_col else ""
        out["price"] = pd.to_numeric(df[price_col], errors="coerce") if price_col else pd.NA
        out["total_value"] = pd.NA
        return out
