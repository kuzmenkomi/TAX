from __future__ import annotations

import os
from typing import Any

import pandas as pd

from app.accounting.avco_engine import compute_pnl_avco, compute_income_events
from app.accounting.price_fill import fill_missing_prices
from app.accounting.pricing import PriceService
from app.accounting.rp2_calculator import compute_pnl_with_rp2
from app.accounting.tax_loss_harvesting import generate_loss_harvesting_report
from app.config.settings import AppConfig, MatchingConfig, ReportingConfig, TaxConfig
from app.exporters.rp2_ods_exporter import export_to_rp2_ods
from app.ingestion.registry import AdapterRegistry
from app.matching.service import match_transfers
from app.normalization.dedup import deduplicate_transactions
from app.normalization.normalizer import group_swaps, normalize
from app.quality.issues import collect_data_issues
from app.tax.br_compliance import (
    add_p2p_flags,
    add_offshore_flag,
    build_tax_savings_opportunities,
    compute_offshore_onshore_tax_summary,
)
from app.tax.br_reports import compute_darf_projection, compute_monthly_sales_brl
from app.tax.capabilities import is_method_allowed


def run_tax_pipeline(
    raw: pd.DataFrame,
    *,
    format_name: str,
    accounting_method: str,
    country: str,
    max_amount_diff: float,
    max_time_diff_seconds: int,
    quote_currency: str,
    use_ptax: bool,
    source_provider: str | None,
    output_dir: str,
    tax_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = AppConfig(
        matching=MatchingConfig(
            max_amount_diff=max_amount_diff,
            max_time_diff_seconds=max_time_diff_seconds,
        ),
        tax=TaxConfig(
            accounting_method=accounting_method,
            base_currency="BRL" if quote_currency.upper() == "BRL" else "USD",
        ),
        reporting=ReportingConfig(
            output_dir=output_dir,
            write_json=True,
            write_csv=True,
            write_summary=True,
        ),
    )

    df = raw
    if format_name != "native":
        adapter = AdapterRegistry.get_adapter(format_name)
        df = adapter.transform(df)

    normalized = normalize(df)
    normalized = group_swaps(normalized)
    normalized = add_offshore_flag(normalized, source_provider=source_provider)
    normalized = add_p2p_flags(normalized)
    price_svc = PriceService(quote_currency=quote_currency, use_ptax=use_ptax)
    normalized = fill_missing_prices(normalized, price_svc)
    from app.accounting.price_fill import add_synthetic_opening_balances
    normalized = add_synthetic_opening_balances(normalized, price_svc)
    normalized, dedup_info = deduplicate_transactions(normalized)
    
    # 2. Recognize DeFi Protocols (LP, Lending, Staking)
    from app.integrations.defi_recognizer import recognize_defi_events, classify_for_tax
    normalized = recognize_defi_events(normalized)
    normalized = classify_for_tax(normalized)
    
    # 3. Match Transfers
    matches = match_transfers(normalized, cfg.matching)

    dedup_removed = 0
    if isinstance(dedup_info, dict):
        dedup_removed = int(dedup_info.get("dropped", 0) or 0)

    paths = export_to_rp2_ods(normalized, matches, cfg.reporting.output_dir)
    method = (cfg.tax.accounting_method or "FIFO").upper()
    country_norm = (country or "br").lower()
    if not is_method_allowed(country_norm, method):
        method = "AVCO" if country_norm in ("uk", "de", "br") else "FIFO"

    if method == "AVCO":
        pnl = compute_pnl_avco(normalized)
        pnl["country"] = country_norm
        pnl["quote_currency"] = quote_currency.upper()
    else:
        from app.accounting.calculator import calculate_pnl, TaxRules
        rules = TaxRules(**tax_rules) if tax_rules else TaxRules()
        pnl = calculate_pnl(normalized, matches, price_svc, rules=rules)
        pnl["engine"] = "taxflow_native"
        pnl["country"] = country_norm
        pnl["quote_currency"] = quote_currency.upper()

    issues = collect_data_issues(
        normalized,
        dedup_removed=dedup_removed,
        matches_found=len(matches),
    )
    
    # Extract income recognition events (STAKING, AIRDROP, LENDING, etc.)
    income_result = compute_income_events(normalized)
    
    # Build current prices dict for loss harvesting analysis
    # Use the price_svc to get latest prices for all assets in inventory
    current_prices = {}
    pnl_inventory = pnl.get("inventory", {})
    for asset in pnl_inventory.keys():
        try:
            # Get latest price from PriceService
            price = price_svc.get_price(asset, quote_currency=quote_currency)
            if price and price > 0:
                current_prices[asset.lower()] = price
        except Exception:
            # If price lookup fails, use last known price from normalization
            latest_tx = normalized[normalized["asset"] == asset].iloc[-1:] if (normalized["asset"] == asset).any() else None
            if latest_tx is not None and len(latest_tx) > 0:
                current_prices[asset.lower()] = float(latest_tx.iloc[0].get("price", 0) or 0)
    
    # Generate tax loss harvesting recommendations
    loss_harvesting = generate_loss_harvesting_report(
        normalized,
        current_prices,
        tax_rate=0.15,  # 15% assumed marginal tax rate
    )
    
    monthly_sales_brl = compute_monthly_sales_brl(normalized)
    
    # Calculate monthly realized gains, losses, and taxes
    from datetime import datetime
    monthly_gains = {}
    monthly_losses = {}
    
    lot_matches = pnl.get("lot_matches", [])
    for match in lot_matches:
        ts = match.get("sell_timestamp")
        if not ts:
            continue
        if not isinstance(ts, datetime):
            try:
                ts = pd.Timestamp(ts).to_pydatetime()
            except Exception:
                continue
        ym = ts.strftime("%Y-%m")
        gain_loss = float(match.get("gain_loss", 0.0) or 0.0)
        
        if gain_loss > 0:
            monthly_gains[ym] = monthly_gains.get(ym, 0.0) + gain_loss
        else:
            monthly_losses[ym] = monthly_losses.get(ym, 0.0) + abs(gain_loss)
            
    from app.accounting.tax_estimate import compute_tax_liability

    total_tax, monthly_tax_owed = compute_tax_liability(
        country=country_norm.upper(),
        monthly_gains=monthly_gains,
        monthly_losses=monthly_losses,
        monthly_sales_brl=monthly_sales_brl,
    )

    pnl["monthly_gains"] = monthly_gains
    pnl["monthly_losses"] = monthly_losses
    pnl["monthly_tax_owed"] = monthly_tax_owed
    pnl["total_tax_owed_usd"] = float(total_tax)
    
    darf = compute_darf_projection(pnl, monthly_sales_brl)
    offshore_onshore = compute_offshore_onshore_tax_summary(normalized, pnl, monthly_sales_brl)
    tax_savings = build_tax_savings_opportunities(normalized)
    p2p_count = int(normalized.get("is_p2p_self_custody", pd.Series([], dtype=bool)).sum()) if "is_p2p_self_custody" in normalized.columns else 0

    return {
        "normalized": normalized,
        "matches": matches,
        "dedup": dedup_info,
        "pnl": pnl,
        "issues": issues,
        "income_events": income_result,
        "loss_harvesting": loss_harvesting,
        "monthly_sales_brl": monthly_sales_brl,
        "isencao_threshold_brl": 35000.0,
        "darf": darf,
        "offshore_onshore": offshore_onshore,
        "tax_savings_opportunities": tax_savings,
        "p2p_self_custody_count": p2p_count,
        "use_ptax": bool(use_ptax),
        "rows_processed": len(normalized),
        "matches_found": len(matches),
        "paths": paths,
        "accounting_method_used": method,
    }


def save_normalized_csv(normalized: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    normalized.to_csv(path, index=False)
