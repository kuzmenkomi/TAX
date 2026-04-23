from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.accounting.pricing import PriceService


def _build_sale_lines(df: pd.DataFrame, accounting_method: str, use_ptax: bool) -> list[str]:
    buys: dict[str, list[tuple[pd.Timestamp, float, float]]] = defaultdict(list)
    lines: list[str] = []
    price = PriceService(quote_currency="BRL", use_ptax=use_ptax)

    for _, row in df.sort_values("timestamp").iterrows():
        t = str(row.get("type", "")).upper()
        asset = str(row.get("asset", "")).upper()
        ts = pd.Timestamp(row.get("timestamp"))
        amount = float(row.get("amount", 0.0) or 0.0)
        px = float(row.get("price", 0.0) or 0.0)
        if t in {"BUY", "IN", "RECEIVE", "DEPOSIT", "INTEREST", "STAKING", "AIRDROP"}:
            buys[asset].append((ts, amount, px))
        elif t in {"SELL", "OUT", "WITHDRAW"} and amount > 0:
            ptax_sell = price._ptax_usd_brl(ts.timestamp()) if use_ptax else 0.0
            chunks = buys.get(asset, [])[:2]
            chunks_text = "; ".join(
                [f"{q:.6f} {asset} ({d.strftime('%Y-%m-%d')}, preco {p:.2f})" for d, q, p in chunks]
            ) or "sem lotes rastreados"
            line = (
                f"Vendido {amount:.6f} {asset} em {ts.strftime('%Y-%m-%d')} preco {px:.2f}. "
                f"Lotes origem: {chunks_text}. Metodo: {accounting_method}. PTAX venda: {ptax_sell:.4f}"
            )
            lines.append(line)
    return lines


def generate_audit_pdf(
    normalized: pd.DataFrame,
    out_path: str,
    *,
    accounting_method: str,
    use_ptax: bool,
) -> None:
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, y, "Audit Log - Receita Federal Support")
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, y, f"Metodo: {accounting_method} | PTAX: {'sim' if use_ptax else 'nao'}")
    y -= 10 * mm

    for line in _build_sale_lines(normalized, accounting_method, use_ptax):
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 9)
        c.drawString(15 * mm, y, line[:150])
        y -= 6 * mm
    c.save()

