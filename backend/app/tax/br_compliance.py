from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import pandas as pd

ONSHORE_PROVIDERS = {"mercado_bitcoin", "foxbit", "novadax"}
STABLES = {"USDT", "USDC", "DAI", "BUSD", "PYUSD"}


def classify_is_offshore(wallet_or_provider: str | None) -> bool:
    p = (wallet_or_provider or "").strip().lower()
    if not p:
        return True
    return p not in ONSHORE_PROVIDERS


def add_offshore_flag(df: pd.DataFrame, *, source_provider: str | None = None) -> pd.DataFrame:
    out = df.copy()
    if "is_offshore" in out.columns:
        return out
    if source_provider:
        out["is_offshore"] = bool(classify_is_offshore(source_provider))
        return out
    out["is_offshore"] = out.get("from_wallet", "").astype(str).apply(classify_is_offshore)
    return out


def add_p2p_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "is_p2p_self_custody" in out.columns:
        return out
    fiat_assets = {"BRL", "USD", "USDT", "USDC"}
    flags = []
    for _, row in out.iterrows():
        tx_type = str(row.get("type", "")).upper()
        asset = str(row.get("asset", "")).upper()
        from_w = str(row.get("from_wallet", "")).strip().lower()
        to_w = str(row.get("to_wallet", "")).strip().lower()
        no_counterparty = (not from_w or from_w in {"unknown", "external"}) or (not to_w or to_w in {"unknown", "external"})
        is_fiat_leg = asset in fiat_assets
        p2p_like = tx_type in {"RECEIVE", "TRANSFER", "BUY", "SELL"} and no_counterparty and is_fiat_leg
        flags.append(bool(p2p_like))
    out["is_p2p_self_custody"] = flags
    out["decripto_channel"] = out["is_p2p_self_custody"].map(lambda x: "DIRECT" if x else "EXCHANGE")
    return out


def _progressive_onshore_rate(gain_brl: float) -> float:
    if gain_brl <= 5_000_000:
        return 0.15
    if gain_brl <= 10_000_000:
        return 0.175
    if gain_brl <= 30_000_000:
        return 0.20
    return 0.225


def compute_offshore_onshore_tax_summary(
    df: pd.DataFrame,
    pnl: dict[str, Any],
    monthly_sales_brl: dict[str, float],
    *,
    threshold_brl: float = 35_000.0,
) -> dict[str, Any]:
    if df.empty:
        return {}
    total_sales = max(sum(float(v or 0.0) for v in monthly_sales_brl.values()), 0.0)
    offshore_sales = 0.0
    onshore_sales = 0.0
    monthly_offshore_sales: dict[str, float] = defaultdict(float)
    monthly_onshore_sales: dict[str, float] = defaultdict(float)
    for _, row in df.iterrows():
        tx_type = str(row.get("type", "")).upper()
        if tx_type not in {"SELL", "OUT", "WITHDRAW", "SWAP", "TRADE"}:
            continue
        ts = row.get("timestamp")
        if pd.isna(ts):
            continue
        month = pd.Timestamp(ts).strftime("%Y-%m")
        qty = float(row.get("amount_out", row.get("amount", 0.0)) or 0.0)
        price = float(row.get("price", 0.0) or 0.0)
        sale = max(qty * price, 0.0)
        if bool(row.get("is_offshore", True)):
            offshore_sales += sale
            monthly_offshore_sales[month] += sale
        else:
            onshore_sales += sale
            monthly_onshore_sales[month] += sale

    total_realized = float(pnl.get("total_realized_pnl_usd", 0.0) or 0.0)
    offshore_gain = total_realized * (offshore_sales / total_sales) if total_sales > 0 else total_realized
    onshore_gain = total_realized - offshore_gain

    offshore_tax = max(offshore_gain, 0.0) * 0.15
    latest_month = sorted(monthly_sales_brl.keys())[-1] if monthly_sales_brl else ""
    latest_onshore_sales = float(monthly_onshore_sales.get(latest_month, 0.0))
    latest_offshore_sales = float(monthly_offshore_sales.get(latest_month, 0.0))
    onshore_taxable = latest_onshore_sales > threshold_brl and onshore_gain > 0
    onshore_rate = _progressive_onshore_rate(max(onshore_gain, 0.0)) if onshore_taxable else 0.0
    onshore_tax = max(onshore_gain, 0.0) * onshore_rate if onshore_taxable else 0.0
    decripto_required = latest_offshore_sales > threshold_brl

    return {
        "offshore_sales_brl": offshore_sales,
        "onshore_sales_brl": onshore_sales,
        "offshore_gain_brl": offshore_gain,
        "onshore_gain_brl": onshore_gain,
        "offshore_tax_rate": 0.15,
        "offshore_tax_brl": round(offshore_tax, 2),
        "onshore_tax_rate": onshore_rate,
        "onshore_tax_brl": round(onshore_tax, 2),
        "decripto_required": decripto_required,
        "decripto_threshold_brl": threshold_brl,
        "decripto_alert": (
            "Atencao! Voce ultrapassou o limite DeCripto, precisa enviar o relatorio mensal no e-CAC."
            if decripto_required
            else ""
        ),
        "latest_month": latest_month,
        "latest_month_onshore_sales_brl": latest_onshore_sales,
        "latest_month_offshore_sales_brl": latest_offshore_sales,
    }


def build_decripto_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        ts = row.get("timestamp")
        if pd.isna(ts):
            continue
        tx_type = str(row.get("type", "")).upper()
        op_type = tx_type
        if tx_type in {"INTEREST", "STAKING", "AIRDROP", "LENDING", "MINING"}:
            op_type = "INCOME"
        rows.append(
            {
                "data": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                "mes_referencia": pd.Timestamp(ts).strftime("%Y-%m"),
                "tipo_operacao": op_type,
                "ativo": str(row.get("asset", "")).upper(),
                "quantidade": float(row.get("amount", 0.0) or 0.0),
                "valor_brl": round(float(row.get("total_value", 0.0) or 0.0), 2),
                "is_offshore": bool(row.get("is_offshore", True)),
                "canal": str(row.get("decripto_channel", "EXCHANGE")),
                "p2p_self_custody": bool(row.get("is_p2p_self_custody", False)),
                "tx_hash": str(row.get("external_id", "") or ""),
            }
        )
    return rows


def build_dirpf_rows(df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    if df.empty:
        return {"bens_direitos": [], "rendimentos_tributaveis": []}
    last_year = int(pd.Timestamp(df["timestamp"].max()).year)
    cutoff = pd.Timestamp(datetime(last_year, 12, 31))
    dfx = df[pd.to_datetime(df["timestamp"]) <= cutoff].copy()

    position_qty: dict[str, float] = defaultdict(float)
    position_cost: dict[str, float] = defaultdict(float)
    income_rows: list[dict[str, Any]] = []
    for _, row in dfx.iterrows():
        tx_type = str(row.get("type", "")).upper()
        asset = str(row.get("asset", "")).upper()
        amount = float(row.get("amount", 0.0) or 0.0)
        total_value = float(row.get("total_value", 0.0) or 0.0)
        if tx_type in {"BUY", "IN", "RECEIVE", "DEPOSIT"}:
            position_qty[asset] += amount
            position_cost[asset] += max(total_value, 0.0)
        elif tx_type in {"SELL", "OUT", "WITHDRAW"}:
            position_qty[asset] -= amount
        elif tx_type in {"INTEREST", "STAKING", "AIRDROP", "LENDING", "MINING"}:
            income_rows.append(
                {
                    "ano": last_year,
                    "tipo": tx_type,
                    "ativo": asset,
                    "valor_brl": round(max(total_value, 0.0), 2),
                }
            )
            position_qty[asset] += amount
            position_cost[asset] += max(total_value, 0.0)

    bens_rows: list[dict[str, Any]] = []
    for asset, qty in sorted(position_qty.items()):
        if qty <= 0:
            continue
        if asset == "BTC":
            code = "01"
        elif asset in STABLES:
            code = "03"
        elif "NFT" in asset:
            code = "10"
        else:
            code = "82"
        bens_rows.append(
            {
                "ano": last_year,
                "grupo_dirpf": "08",
                "codigo_dirpf": "82",
                "subcodigo_ativo": code,
                "ativo": asset,
                "quantidade": round(qty, 8),
                "custo_aquisicao_brl": round(position_cost.get(asset, 0.0), 2),
            }
        )
    return {"bens_direitos": bens_rows, "rendimentos_tributaveis": income_rows}


def build_tax_savings_opportunities(df: pd.DataFrame, tax_rate: float = 0.15) -> list[dict[str, Any]]:
    if df.empty:
        return []
    # heuristic: assets with net negative realized PnL are likely tax-loss candidates
    by_asset: dict[str, float] = defaultdict(float)
    for _, row in df.iterrows():
        tx_type = str(row.get("type", "")).upper()
        if tx_type not in {"SELL", "OUT", "WITHDRAW"}:
            continue
        asset = str(row.get("asset", "")).upper()
        amount = float(row.get("amount", 0.0) or 0.0)
        price = float(row.get("price", 0.0) or 0.0)
        fees = float(row.get("fee", 0.0) or 0.0) * price
        proceeds = amount * price - fees
        # simplified fallback cost proxy (80% of proceeds)
        cost_proxy = proceeds * 0.8
        by_asset[asset] += proceeds - cost_proxy
    out = []
    for asset, pnl in sorted(by_asset.items(), key=lambda x: x[1]):
        if pnl >= 0:
            continue
        save = abs(pnl) * tax_rate
        out.append(
            {
                "asset": asset,
                "estimated_loss_brl": round(abs(pnl), 2),
                "estimated_tax_saving_brl": round(save, 2),
                "message_pt": f"Venda {asset} ate o fim do mes para potencial economia de {save:.2f} BRL em imposto.",
            }
        )
    return out[:5]

