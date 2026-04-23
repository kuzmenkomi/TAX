from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def export_to_rp2_csv(df: pd.DataFrame, matches: list[dict[str, Any]], output_dir: str = "output") -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    internal_transfer_ids = {int(m["transfer_index"]) for m in matches}
    receive_to_transfer = {int(m["receive_index"]): int(m["transfer_index"]) for m in matches}

    in_rows: list[dict[str, Any]] = []
    out_rows: list[dict[str, Any]] = []
    intra_rows: list[dict[str, Any]] = []

    for idx, tx in df.sort_values("timestamp").iterrows():
        tx_type = str(tx["type"])
        timestamp = _format_timestamp(tx["timestamp"])
        asset = str(tx.get("asset", ""))
        price = _as_float(tx.get("price", 0.0))
        amount = _as_float(tx.get("amount", 0.0))
        fee = _as_float(tx.get("fee", 0.0))
        total_value = _as_float(tx.get("total_value", 0.0))
        unique_id = str(tx.get("external_id", "")) or f"row_{idx}"

        if tx_type == "BUY":
            in_rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "exchange": _wallet_or_unknown(tx.get("to_wallet")),
                "holder": "self",
                "transaction_type": "BUY",
                "spot_price": price,
                "crypto_in": amount,
                "crypto_fee": fee,
                "fiat_in_no_fee": total_value,
                "fiat_in_with_fee": total_value + (fee * price),
                "fiat_fee": fee * price,
                "unique_id": unique_id,
                "notes": "Exported from MVP parser",
            })

        elif tx_type == "SELL":
            out_rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "exchange": _wallet_or_unknown(tx.get("from_wallet")),
                "holder": "self",
                "transaction_type": "SELL",
                "spot_price": price,
                "crypto_out_no_fee": amount,
                "crypto_fee": fee,
                "crypto_out_with_fee": amount + fee,
                "fiat_out_no_fee": total_value,
                "fiat_fee": fee * price,
                "unique_id": unique_id,
                "notes": "Exported from MVP parser",
            })

        # ИСПРАВЛЕНО: добавлена обработка SWAP и TRADE
        # Своп = продажа asset_out + покупка asset_in
        elif tx_type in ["SWAP", "TRADE"]:
            asset_out = str(tx.get("asset_out", asset))
            amount_out = _as_float(tx.get("amount_out", amount))
            asset_in = str(tx.get("asset_in", ""))
            amount_in = _as_float(tx.get("amount_in", 0.0))
            swap_id = unique_id

            # Продажа стороны OUT
            out_rows.append({
                "timestamp": timestamp,
                "asset": asset_out,
                "exchange": _wallet_or_unknown(tx.get("from_wallet")),
                "holder": "self",
                "transaction_type": "SELL",
                "spot_price": price,
                "crypto_out_no_fee": amount_out,
                "crypto_fee": fee,
                "crypto_out_with_fee": amount_out + fee,
                "fiat_out_no_fee": total_value,
                "fiat_fee": fee * price,
                "unique_id": f"{swap_id}_out",
                "notes": f"SWAP out leg: {asset_out} → {asset_in}",
            })

            # Покупка стороны IN
            if asset_in and amount_in > 0:
                in_rows.append({
                    "timestamp": timestamp,
                    "asset": asset_in,
                    "exchange": _wallet_or_unknown(tx.get("to_wallet")),
                    "holder": "self",
                    "transaction_type": "BUY",
                    "spot_price": 0.0,  # цена рассчитывается через proceeds
                    "crypto_in": amount_in,
                    "crypto_fee": 0.0,  # комиссия уже учтена в out leg
                    "fiat_in_no_fee": total_value,
                    "fiat_in_with_fee": total_value,
                    "fiat_fee": 0.0,
                    "unique_id": f"{swap_id}_in",
                    "notes": f"SWAP in leg: {asset_out} → {asset_in}",
                })

        elif tx_type == "TRANSFER" and int(idx) in internal_transfer_ids:
            intra_rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "from_exchange": _wallet_or_unknown(tx.get("from_wallet")),
                "from_holder": "self",
                "to_exchange": _wallet_or_unknown(tx.get("to_wallet")),
                "to_holder": "self",
                "spot_price": price,
                "crypto_sent": amount,
                "crypto_received": amount - fee,
                "unique_id": unique_id,
                "notes": "Matched internal transfer",
            })

        elif tx_type == "RECEIVE" and int(idx) in receive_to_transfer:
            # Пропускаем — это вторая нога внутреннего перевода
            continue

    in_file = output_path / "rp2_in_transactions.csv"
    out_file = output_path / "rp2_out_transactions.csv"
    intra_file = output_path / "rp2_intra_transactions.csv"
    pd.DataFrame(in_rows).to_csv(in_file, index=False)
    pd.DataFrame(out_rows).to_csv(out_file, index=False)
    pd.DataFrame(intra_rows).to_csv(intra_file, index=False)

    return {"in": str(in_file), "out": str(out_file), "intra": str(intra_file)}


def _as_float(value: Any) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _wallet_or_unknown(value: Any) -> str:
    wallet = str(value or "").strip()
    return wallet if wallet else "Unknown"


def _format_timestamp(value: Any) -> str:
    ts = pd.Timestamp(value)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return ts.isoformat()