from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _month_key(value: Any) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.strftime("%Y-%m")


def compute_monthly_sales_brl(df: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {}
    for _, row in df.iterrows():
        tx_type = str(row.get("type", "")).upper()
        if tx_type not in {"SELL", "OUT", "WITHDRAW", "SWAP", "TRADE"}:
            continue
        ts = row.get("timestamp")
        if pd.isna(ts):
            continue
        if tx_type in {"SWAP", "TRADE"}:
            value = float(row.get("amount_out", 0.0) or 0.0) * float(row.get("price", 0.0) or 0.0)
        else:
            value = float(row.get("amount", 0.0) or 0.0) * float(row.get("price", 0.0) or 0.0)
        if value <= 0:
            continue
        key = _month_key(ts)
        out[key] = out.get(key, 0.0) + value
    return out


def compute_darf_projection(
    pnl: dict[str, Any],
    monthly_sales_brl: dict[str, float],
    *,
    tax_rate: float = 0.15,
    threshold_brl: float = 35000.0,
) -> dict[str, Any] | None:
    if not monthly_sales_brl:
        return None

    month = sorted(monthly_sales_brl.keys())[-1]
    sales = float(monthly_sales_brl.get(month, 0.0) or 0.0)
    net = float(pnl.get("total_realized_pnl_usd", 0.0) or 0.0)
    taxable = sales > threshold_brl and net > 0.0
    amount = round(net * tax_rate, 2) if taxable else 0.0

    year, mon = month.split("-")
    y, m = int(year), int(mon)
    due_month = m + 1
    due_year = y
    if due_month > 12:
        due_month = 1
        due_year += 1
    due_day = monthrange(due_year, due_month)[1]
    due_date = datetime(due_year, due_month, due_day, tzinfo=timezone.utc).strftime("%d.%m.%Y")
    return {
        "month": month,
        "sales_brl": sales,
        "code": "4600",
        "taxable": taxable,
        "amount_brl": amount,
        "due_date": due_date,
        "message_pt": f"Neste mês você precisa pagar DARF de {amount:.2f} BRL. Vencimento: até {due_date}.",
    }


def build_gcap_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        tx_type = str(row.get("type", "")).upper()
        if tx_type not in {"SELL", "OUT", "WITHDRAW"}:
            continue
        ts = row.get("timestamp")
        if pd.isna(ts):
            continue
        amount = float(row.get("amount", 0.0) or 0.0)
        price = float(row.get("price", 0.0) or 0.0)
        fee = float(row.get("fee", 0.0) or 0.0)
        gross = amount * price
        net = gross - fee * price
        rows.append(
            {
                "Data da Operacao": pd.Timestamp(ts).strftime("%d/%m/%Y"),
                "Bem": str(row.get("asset", "")).upper(),
                "Quantidade": round(amount, 8),
                "Valor de Venda (BRL)": round(gross, 2),
                "Taxas (BRL)": round(fee * price, 2),
                "Valor Liquido (BRL)": round(net, 2),
            }
        )
    return rows
