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


SUPPORTED_EXCHANGE_IDS: dict[str, str] = {
    "binance": "binance",
    "coinbase": "coinbasepro",
    "coinbasepro": "coinbasepro",
    "kraken": "kraken",
    "okx": "okx",
    "mercado_bitcoin": "mercadobitcoin",
    "foxbit": "foxbit",
    "novadax": "novadax",
}

DEFAULT_SYMBOLS_BY_PROVIDER: dict[str, list[str]] = {
    "binance": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "coinbase": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "kraken": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "okx": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "mercado_bitcoin": ["BTC/BRL", "ETH/BRL", "SOL/BRL"],
    "foxbit": ["BTC/BRL", "ETH/BRL", "SOL/BRL"],
    "novadax": ["BTC/BRL", "ETH/BRL", "SOL/BRL"],
}


def fetch_exchange_spot_trades_dataframe(
    provider: str,
    api_key: str,
    api_secret: str,
    *,
    symbols: list[str] | None = None,
    limit_per_symbol: int = 200,
) -> pd.DataFrame:
    if ccxt is None:
        raise RuntimeError("ccxt is not installed. Run: pip install ccxt") from _CCXT_ERR

    provider_norm = (provider or "").strip().lower()
    exchange_id = SUPPORTED_EXCHANGE_IDS.get(provider_norm)
    if not exchange_id:
        raise RuntimeError(f"Unsupported provider: {provider}")

    if not hasattr(ccxt, exchange_id):
        raise RuntimeError(f"ccxt exchange '{exchange_id}' not available in installed ccxt version")

    exchange_class = getattr(ccxt, exchange_id)
    ex = exchange_class(
        {
            "apiKey": api_key.strip(),
            "secret": api_secret.strip(),
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
    )

    syms = symbols if symbols else DEFAULT_SYMBOLS_BY_PROVIDER.get(provider_norm, ["BTC/USDT"])
    rows: list[dict[str, Any]] = []

    for sym in syms:
        symbol = (sym or "").strip()
        if not symbol:
            continue
        try:
            trades = ex.fetch_my_trades(symbol, limit=limit_per_symbol)
        except Exception:
            continue

        base = symbol.split("/")[0].upper() if "/" in symbol else symbol.upper()
        for t in trades:
            side = str(t.get("side") or "").upper()
            tx_type = "BUY" if side == "BUY" else "SELL" if side == "SELL" else None
            if tx_type is None:
                continue
            fee_info = t.get("fee") or {}
            fee = float(fee_info.get("cost") or 0.0)
            fee_ccy = str(fee_info.get("currency") or base).upper()
            ts = t.get("timestamp")
            if ts is None:
                continue
            amount = float(t.get("amount") or 0.0)
            price = float(t.get("price") or 0.0)
            cost = float(t.get("cost") or 0.0) or (amount * price)
            rows.append(
                {
                    "timestamp": pd.Timestamp(int(ts), unit="ms", tz="UTC"),
                    "asset": base,
                    "type": tx_type,
                    "amount": amount,
                    "fee": fee,
                    "fee_asset": fee_ccy,
                    "from_wallet": provider_norm,
                    "to_wallet": provider_norm,
                    "price": price,
                    "total_value": cost,
                    "external_id": f"{provider_norm}:{t.get('id', '')}",
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

