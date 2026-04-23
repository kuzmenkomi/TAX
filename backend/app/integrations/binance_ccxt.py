from __future__ import annotations

from typing import Any

import pandas as pd

try:
    import ccxt  # type: ignore
except ImportError as e:  # pragma: no cover
    ccxt = None  # type: ignore
    _CCXT_ERR = e
else:
    _CCXT_ERR = None

# Common pairs for BR users (USDT markets). User can override.
DEFAULT_SYMBOLS: list[str] = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "MATIC/USDT",
    "AVAX/USDT",
    "LINK/USDT",
    "DOT/USDT",
    "LTC/USDT",
    "ATOM/USDT",
    "NEAR/USDT",
    "APT/USDT",
]


def fetch_binance_spot_trades_dataframe(
    api_key: str,
    api_secret: str,
    *,
    symbols: list[str] | None = None,
    limit_per_symbol: int = 200,
) -> pd.DataFrame:
    """
    Pull recent spot trades via ccxt (read-only API keys).
    Binance requires per-symbol myTrades; we iterate the given symbol list.
    """
    if ccxt is None:
        raise RuntimeError("ccxt is not installed. Run: pip install ccxt") from _CCXT_ERR

    ex = ccxt.binance(
        {
            "apiKey": api_key.strip(),
            "secret": api_secret.strip(),
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
    )
    syms = symbols if symbols else DEFAULT_SYMBOLS
    rows: list[dict[str, Any]] = []

    for sym in syms:
        sym = sym.strip()
        if not sym:
            continue
        try:
            trades = ex.fetch_my_trades(sym, limit=limit_per_symbol)
        except Exception:
            continue
        base = sym.split("/")[0].upper() if "/" in sym else sym
        for t in trades:
            side = str(t.get("side") or "").upper()
            typ = "BUY" if side == "BUY" else "SELL"
            fee_info = t.get("fee") or {}
            fee = float(fee_info.get("cost") or 0)
            fee_ccy = str(fee_info.get("currency") or base).upper()
            ts = t.get("timestamp")
            if ts is None:
                continue
            rows.append(
                {
                    "timestamp": pd.Timestamp(int(ts), unit="ms", tz="UTC"),
                    "asset": base,
                    "type": typ,
                    "amount": float(t.get("amount") or 0),
                    "fee": fee,
                    "fee_asset": fee_ccy,
                    "from_wallet": "binance",
                    "to_wallet": "binance",
                    "price": float(t.get("price") or 0),
                    "total_value": float(t.get("cost") or 0)
                    or (float(t.get("price") or 0) * float(t.get("amount") or 0)),
                    "external_id": f"binance:{t.get('id', '')}",
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "asset",
                "type",
                "amount",
                "fee",
                "fee_asset",
                "from_wallet",
                "to_wallet",
                "price",
                "total_value",
                "external_id",
            ]
        )

    out = pd.DataFrame(rows)
    out = out.sort_values("timestamp").reset_index(drop=True)
    return out
