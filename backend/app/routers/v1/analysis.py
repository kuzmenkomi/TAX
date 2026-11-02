from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.accounting.avco_engine import compute_pnl_avco
from app.accounting.tax_estimate import compute_tax_liability
from app.accounting.price_fill import fill_missing_prices
from app.accounting.pricing import PriceService
from app.accounting.rp2_calculator import compute_pnl_with_rp2
from app.auth import get_current_user
from app.config.settings import load_config
from app.core.db import get_db
from app.ingestion.csv_loader import load_csv
from app.ingestion.registry import AdapterRegistry
from app.matching.service import match_transfers
from app.models import AnalysisRun, ImportJob, User
from app.normalization.dedup import deduplicate_transactions
from app.normalization.normalizer import group_swaps, normalize
from app.exporters.rp2_ods_exporter import export_to_rp2_ods
from app.schemas.analysis import AnalyzeRequest, AnalysisResultResponse, MultiAnalysisResultResponse
from app.services.analysis_service import (
    analyze_from_dataframe,
    list_runs,
    persist_run,
    run_analysis_from_upload,
)
from app.tax.capabilities import is_method_allowed

router = APIRouter(tags=["analysis"])
BACKEND_ROOT = Path(__file__).resolve().parents[3]

COUNTRY_QUOTE_CURRENCY: dict[str, str] = {
    "us": "USD",
    "mx": "MXN",
    "br": "BRL",
    "ar": "ARS",
    "co": "COP",
    "pe": "PEN",
    "cl": "CLP",
    "gt": "GTQ",
    "ec": "USD",
    "uy": "UYU",
    "cr": "CRC",
    "hn": "HNL",
    "bo": "BOB",
}


class SourceAnalysisRequest(BaseModel):
    source_ids: list[str]
    accounting_method: str = "FIFO"
    country: str = "br"
    use_ptax: bool = False
    auto_classify: bool = False


def _run_csv_path(run: AnalysisRun) -> Path:
    csv_path = Path(run.csv_rel_path)
    if not csv_path.is_absolute():
        csv_path = BACKEND_ROOT / csv_path
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"Source data for run {run.id} not found")
    return csv_path


def _wallet_transactions_df(db: Session, user_id: int, wallet_id: int) -> pd.DataFrame:
    from app.models.transaction import Transaction

    rows = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.from_wallet == str(wallet_id),
        )
        .order_by(Transaction.timestamp.asc())
        .all()
    )
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "timestamp": row.timestamp,
                "asset": row.asset,
                "type": row.tx_type,
                "amount": float(row.amount),
                "fee": float(row.fee or 0),
                "price": float(row.price) if row.price is not None else None,
                "total_value": float(row.total_value) if row.total_value is not None else None,
                "from_wallet": row.from_wallet or "",
                "to_wallet": row.to_wallet or "",
                "external_id": row.external_id or "",
                "audit_hash": row.audit_hash or "",
            }
            for row in rows
        ]
    )


def _user_transactions_df(db: Session, user_id: int) -> pd.DataFrame:
    from app.models.transaction import Transaction

    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        .all()
    )
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "timestamp": row.timestamp,
                "asset": row.asset,
                "type": row.tx_type,
                "amount": float(row.amount),
                "fee": float(row.fee or 0),
                "price": float(row.price) if row.price is not None else None,
                "total_value": float(row.total_value) if row.total_value is not None else None,
                "from_wallet": row.from_wallet or "",
                "to_wallet": row.to_wallet or "",
                "external_id": row.external_id or "",
                "audit_hash": row.audit_hash or "",
            }
            for row in rows
        ]
    )


def _resolve_user_country(db: Session, user_id: int, summary_country: str = "") -> str:
    if summary_country:
        return summary_country.strip().upper()
    from app.models import Portfolio

    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if portfolio and portfolio.country_code:
        return str(portfolio.country_code).strip().upper()
    user = db.query(User).filter(User.id == user_id).first()
    if user and getattr(user, "jurisdiction_code", None):
        return str(user.jurisdiction_code).strip().upper()
    return "US"


def _summarize_pnl_for_tax_year(pnl: dict[str, Any], tax_year: int | None, country: str = "US") -> dict[str, Any]:
    if tax_year is None:
        return pnl

    year_prefix = f"{tax_year}-"
    monthly_gains = pnl.get("monthly_gains", {}) if isinstance(pnl.get("monthly_gains"), dict) else {}
    monthly_losses = pnl.get("monthly_losses", {}) if isinstance(pnl.get("monthly_losses"), dict) else {}
    monthly_tax = pnl.get("monthly_tax_owed", {}) if isinstance(pnl.get("monthly_tax_owed"), dict) else {}

    year_gains = sum(float(value or 0) for key, value in monthly_gains.items() if str(key).startswith(year_prefix))
    year_losses = sum(float(value or 0) for key, value in monthly_losses.items() if str(key).startswith(year_prefix))
    year_net = year_gains - year_losses
    year_tax, year_monthly_tax = compute_tax_liability(
        country=country,
        monthly_gains=monthly_gains,
        monthly_losses=monthly_losses,
        monthly_tax_from_run=monthly_tax,
        tax_year=tax_year,
    )

    realized_by_asset: dict[str, float] = {}
    for match in pnl.get("lot_matches", []) or []:
        sell_ts = match.get("sell_timestamp")
        if not sell_ts:
            continue
        try:
            sell_year = pd.Timestamp(sell_ts).year
        except Exception:
            continue
        if sell_year != tax_year:
            continue
        asset = str(match.get("asset") or "").upper()
        if not asset:
            continue
        realized_by_asset[asset] = realized_by_asset.get(asset, 0.0) + float(match.get("gain_loss", 0) or 0)

    return {
        **pnl,
        "total_realized_pnl_usd": year_net,
        "total_realized_loss_usd": year_losses,
        "realized_pnl_by_asset": realized_by_asset,
        "total_tax_owed_usd": year_tax,
        "monthly_tax_owed": year_monthly_tax,
        "tax_year": tax_year,
    }


def _empty_latest_analysis_response() -> dict[str, object]:
    return {
        "status": "empty",
        "pnl": {},
        "capital_gains": 0.0,
        "capital_losses": 0.0,
        "tax_owed": 0.0,
        "monthly_gains": {},
        "monthly_losses": {},
        "rows_processed": 0,
        "matches_found": 0,
    }


def _month_key(value: Any) -> str | None:
    if not value:
        return None
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return None
    if pd.isna(ts):
        return None
    return ts.strftime("%Y-%m")


def _add_amount(bucket: dict[str, float], key: str, amount: Any) -> None:
    bucket[key] = bucket.get(key, 0.0) + float(amount or 0.0)


def _cached_dashboard_analysis(db: Session, user_id: int, tax_year: int | None) -> dict[str, object]:
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == user_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )
    if not runs:
        return _empty_latest_analysis_response()

    monthly_gains: dict[str, float] = {}
    monthly_losses: dict[str, float] = {}
    monthly_tax: dict[str, float] = {}
    realized_by_asset: dict[str, float] = {}
    rows_processed = 0
    matches_found = 0
    latest_run_id = runs[0].id
    quote_currency = ""
    accounting_method = ""
    country_code = ""
    taxable_events_count = 0
    internal_transfer_count = 0
    total_gas_fees = 0.0

    for run in runs:
        try:
            summary = json.loads(run.summary_json or "{}")
        except json.JSONDecodeError:
            continue

        pnl = summary.get("pnl", {}) if isinstance(summary, dict) else {}
        if not isinstance(pnl, dict):
            pnl = {}

        rows_processed += int(summary.get("rows_processed") or summary.get("tx_imported") or 0)
        matches_found += int(summary.get("matches_found") or 0)
        quote_currency = quote_currency or str(summary.get("quote_currency") or "")
        accounting_method = accounting_method or str(summary.get("accounting_method") or "")
        country_code = country_code or str(
            summary.get("country") or summary.get("country_code") or pnl.get("country") or ""
        )

        taxable_events_count += int(pnl.get("taxable_events_count") or 0)
        internal_transfer_count += int(pnl.get("internal_transfer_count") or 0)
        total_gas_fees += float(pnl.get("total_gas_fees_usd") or 0.0)

        run_monthly_gains = pnl.get("monthly_gains")
        run_monthly_losses = pnl.get("monthly_losses")
        run_monthly_tax = pnl.get("monthly_tax_owed")
        lot_matches = pnl.get("lot_matches", []) or []

        # Prefer lot-level matches (captures gains and losses); monthly dicts are a fallback.
        if lot_matches:
            for match in lot_matches:
                key = _month_key(match.get("sell_timestamp"))
                if key is None:
                    continue
                if tax_year is not None and not key.startswith(f"{tax_year}-"):
                    continue

                gain_loss = float(match.get("gain_loss") or 0.0)
                if gain_loss >= 0:
                    _add_amount(monthly_gains, key, gain_loss)
                else:
                    _add_amount(monthly_losses, key, abs(gain_loss))

                asset = str(match.get("asset") or "").upper()
                if asset:
                    realized_by_asset[asset] = realized_by_asset.get(asset, 0.0) + gain_loss
            if isinstance(run_monthly_tax, dict):
                for key, value in run_monthly_tax.items():
                    if tax_year is None or str(key).startswith(f"{tax_year}-"):
                        _add_amount(monthly_tax, str(key), value)
            continue

        if isinstance(run_monthly_gains, dict) or isinstance(run_monthly_losses, dict):
            for key, value in (run_monthly_gains or {}).items():
                if tax_year is None or str(key).startswith(f"{tax_year}-"):
                    _add_amount(monthly_gains, str(key), value)
            for key, value in (run_monthly_losses or {}).items():
                if tax_year is None or str(key).startswith(f"{tax_year}-"):
                    _add_amount(monthly_losses, str(key), value)
            if isinstance(run_monthly_tax, dict):
                for key, value in run_monthly_tax.items():
                    if tax_year is None or str(key).startswith(f"{tax_year}-"):
                        _add_amount(monthly_tax, str(key), value)
            continue

        for match in lot_matches:
            key = _month_key(match.get("sell_timestamp"))
            if key is None:
                continue
            if tax_year is not None and not key.startswith(f"{tax_year}-"):
                continue

            gain_loss = float(match.get("gain_loss") or 0.0)
            if gain_loss >= 0:
                _add_amount(monthly_gains, key, gain_loss)
            else:
                _add_amount(monthly_losses, key, abs(gain_loss))

            asset = str(match.get("asset") or "").upper()
            if asset:
                realized_by_asset[asset] = realized_by_asset.get(asset, 0.0) + gain_loss

    country_code = _resolve_user_country(db, user_id, country_code)
    total_gains = sum(monthly_gains.values())
    total_losses = sum(monthly_losses.values())
    net_pnl = total_gains - total_losses
    total_tax, monthly_tax = compute_tax_liability(
        country=country_code,
        monthly_gains=monthly_gains,
        monthly_losses=monthly_losses,
        monthly_tax_from_run=monthly_tax,
        tax_year=tax_year,
    )

    pnl = {
        "total_realized_pnl_usd": net_pnl,
        "total_realized_loss_usd": total_losses,
        "realized_pnl_by_asset": realized_by_asset,
        "taxable_events_count": taxable_events_count,
        "internal_transfer_count": internal_transfer_count,
        "total_gas_fees_usd": total_gas_fees,
        "monthly_gains": monthly_gains,
        "monthly_losses": monthly_losses,
        "monthly_tax_owed": monthly_tax,
        "total_tax_owed_usd": total_tax,
        "quote_currency": quote_currency,
        "tax_year": tax_year,
        "engine": "cached_analysis_runs",
    }

    return {
        "status": "cached",
        "analysis_run_id": latest_run_id,
        "rows_processed": rows_processed,
        "matches_found": matches_found,
        "accounting_method": accounting_method,
        "quote_currency": quote_currency,
        "pnl": pnl,
        "capital_gains": net_pnl,
        "capital_losses": total_losses,
        "tax_owed": total_tax,
        "monthly_gains": monthly_gains,
        "monthly_losses": monthly_losses,
    }


def _selected_sources_df(db: Session, current_user: User, source_ids: list[str]) -> pd.DataFrame:
    from app.models import ExchangeConnection, WalletConnection

    if not source_ids:
        raise HTTPException(status_code=400, detail="No sources selected")

    frames: list[pd.DataFrame] = []
    loaded_run_ids: set[int] = set()

    for source_id in source_ids:
        if source_id.startswith("csv_"):
            run_id = int(source_id.split("_", 1)[1])
            run = (
                db.query(AnalysisRun)
                .filter(AnalysisRun.id == run_id, AnalysisRun.user_id == current_user.id)
                .first()
            )
            if not run:
                raise HTTPException(status_code=404, detail=f"CSV source {source_id} not found")
            if run.id in loaded_run_ids:
                continue
            frames.append(pd.read_csv(_run_csv_path(run)))
            loaded_run_ids.add(run.id)
            continue

        if source_id.startswith("w_"):
            wallet_id = int(source_id.split("_", 1)[1])
            wallet = (
                db.query(WalletConnection)
                .filter(WalletConnection.id == wallet_id, WalletConnection.user_id == current_user.id)
                .first()
            )
            if not wallet:
                raise HTTPException(status_code=404, detail=f"Wallet source {source_id} not found")
            wallet_df = _wallet_transactions_df(db, current_user.id, wallet_id)
            if not wallet_df.empty:
                frames.append(wallet_df)
            continue

        if source_id.startswith("ex_"):
            exchange_id = int(source_id.split("_", 1)[1])
            exchange = (
                db.query(ExchangeConnection)
                .filter(ExchangeConnection.id == exchange_id, ExchangeConnection.user_id == current_user.id)
                .first()
            )
            if not exchange:
                raise HTTPException(status_code=404, detail=f"Exchange source {source_id} not found")
            provider = (exchange.exchange_name or exchange.provider or "").strip().lower()
            if not provider:
                continue
            runs = (
                db.query(AnalysisRun)
                .filter(
                    AnalysisRun.user_id == current_user.id,
                    AnalysisRun.summary_json.ilike(f'%"format": "{provider}"%'),
                )
                .order_by(AnalysisRun.created_at.asc())
                .all()
            )
            for run in runs:
                if run.id in loaded_run_ids:
                    continue
                frames.append(pd.read_csv(_run_csv_path(run)))
                loaded_run_ids.add(run.id)
            continue

        raise HTTPException(status_code=400, detail=f"Unsupported source id: {source_id}")

    non_empty_frames = [frame for frame in frames if not frame.empty]
    if not non_empty_frames:
        raise HTTPException(status_code=400, detail="Selected sources have no transactions")
    return pd.concat(non_empty_frames, ignore_index=True)


@router.get("/br/runs")
def read_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    from sqlalchemy import func as sa_func
    from app.models.transaction import Transaction

    rows = list_runs(db, current_user, limit=50)

    # Count transactions per run in one query
    run_ids = [r.id for r in rows]
    tx_counts: dict[int, int] = {}
    if run_ids:
        count_rows = (
            db.query(Transaction.run_id, sa_func.count(Transaction.id))
            .filter(Transaction.run_id.in_(run_ids))
            .group_by(Transaction.run_id)
            .all()
        )
        tx_counts = {rid: cnt for rid, cnt in count_rows}

    runs: list[dict[str, object]] = []
    for row in rows:
        try:
            summary = json.loads(row.summary_json or "{}")
        except json.JSONDecodeError:
            summary = {}
        pnl = summary.get("pnl", {}) if isinstance(summary, dict) else {}
        runs.append(
            {
                "run_id": row.id,
                "created_at": str(row.created_at),
                "accounting_method": summary.get("accounting_method", "unknown"),
                "format": summary.get("format", ""),
                "quote_currency": summary.get("quote_currency", ""),
                "realized_pnl": float((pnl or {}).get("total_realized_pnl_usd", 0.0) or 0.0),
                "rows_processed": tx_counts.get(row.id, 0),
            }
        )
    return {"runs": runs}


@router.delete("/br/runs/{run_id}")
def delete_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Delete an analysis run and all its associated transactions."""
    from app.models.transaction import Transaction as TxModel

    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == current_user.id,
    ).first()
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")

    # Cascade-delete linked transactions first
    db.query(TxModel).filter(TxModel.run_id == run_id).delete(synchronize_session=False)
    if run.file_hash:
        db.query(ImportJob).filter(
            ImportJob.user_id == current_user.id,
            ImportJob.file_hash == run.file_hash,
        ).delete(synchronize_session=False)
    db.delete(run)
    db.commit()
    try:
        _run_csv_path(run).unlink(missing_ok=True)
    except Exception:
        pass
    return {"status": "deleted", "run_id": run_id}


@router.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, object]:
    cfg = load_config(payload.config_path)
    raw = load_csv(payload.file_path)
    normalized = normalize(raw)
    normalized = group_swaps(normalized)
    normalized = fill_missing_prices(normalized, PriceService())
    normalized, dedup = deduplicate_transactions(normalized)
    matches = match_transfers(normalized, cfg.matching)

    paths = export_to_rp2_ods(normalized, matches, cfg.reporting.output_dir)
    method = (cfg.tax.accounting_method or "FIFO").upper()
    country = "us"
    if not is_method_allowed(country, method):
        method = "FIFO"

    if method == "AVCO":
        pnl = compute_pnl_avco(normalized)
    else:
        rp2_result = compute_pnl_with_rp2(paths["ini"], paths["ods"], method=method.lower())
        pnl = {
            "total_realized_pnl_usd": rp2_result.total_realized_pnl_usd,
            "realized_pnl_by_asset": rp2_result.realized_pnl_by_asset,
            "taxable_events_count": rp2_result.taxable_events_count,
            "internal_transfer_count": rp2_result.internal_transfer_count,
            "total_gas_fees_usd": rp2_result.total_gas_fees_usd,
            "engine": "rp2",
        }

    return {"matches_found": len(matches), "dedup": dedup, "pnl": pnl}


@router.post("/analyze-upload", response_model=AnalysisResultResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    format: str = Form("native"),
    accounting_method: str = Form("FIFO"),
    max_amount_diff: float = Form(0.01),
    max_time_diff_seconds: int = Form(3600),
    country: str = Form("br"),
    quote_currency: str = Form("BRL"),
    use_ptax: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    result = run_analysis_from_upload(
        db,
        current_user,
        await file.read(),
        file.filename or "upload.csv",
        format_name=format,
        accounting_method=accounting_method,
        country=country,
        quote_currency=quote_currency,
        use_ptax=use_ptax,
        max_amount_diff=max_amount_diff,
        max_time_diff_seconds=max_time_diff_seconds,
    )
    return AnalysisResultResponse.model_validate(result)


@router.post("/analyze-upload-multi", response_model=MultiAnalysisResultResponse)
async def analyze_upload_multi(
    files: list[UploadFile] = File(...),
    format: str = Form("native"),
    accounting_method: str = Form("FIFO"),
    max_amount_diff: float = Form(0.01),
    max_time_diff_seconds: int = Form(3600),
    country: str = Form("br"),
    quote_currency: str = Form("BRL"),
    use_ptax: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MultiAnalysisResultResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    parts: list[pd.DataFrame] = []
    names: list[str] = []
    tmp_paths: list[str] = []

    try:
        for file in files:
            suffix = os.path.splitext(file.filename or "tx.csv")[1] or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_paths.append(tmp.name)
            raw = load_csv(tmp.name, validate_native_schema=(format == "native"))
            if format != "native":
                adapter = AdapterRegistry.get_adapter(format)
                raw = adapter.transform(raw)
            parts.append(raw)
            names.append(file.filename or "file.csv")

        combined = pd.concat(parts, ignore_index=True)
        
        # Enforce transaction limits based on subscription plan
        from app.services.billing_service import get_user_plan, PLAN_LIMITS
        plan = get_user_plan(db, current_user.id)
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        row_count = len(combined)
        if row_count > limits["max_transactions"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "limit_exceeded",
                    "message": f"Your plan ({plan.upper()}) is limited to {limits['max_transactions']} transactions, but these files combined contain {row_count} transactions. Please upgrade to process larger files.",
                    "limit": limits["max_transactions"],
                    "actual": row_count
                }
            )

        result = analyze_from_dataframe(
            combined,
            format_name="native",  # adapters already applied in the loop above
            accounting_method=accounting_method,
            country=country,
            quote_currency=quote_currency,
            use_ptax=use_ptax,
            max_amount_diff=max_amount_diff,
            max_time_diff_seconds=max_time_diff_seconds,
        )

        db.add(
            ImportJob(
                user_id=current_user.id,
                source=f"multi:{format}",
                filename=",".join(names)[:500],
                status="done",
            )
        )
        db.commit()

        run_id = persist_run(
            db,
            current_user.id,
            result["normalized"],
            {
                "issues": result["issues"],
                "pnl": result["pnl"],
                "matches_sample": result["matches"][:20],
                "filenames": ",".join(names),
                "format": format,
                "quote_currency": quote_currency,
                "accounting_method": accounting_method,
                "use_ptax": bool(use_ptax),
            },
        )

        return MultiAnalysisResultResponse.model_validate(
            {
                "status": "ok",
                "filename": names,
                "rows_processed": result["rows_processed"],
                "matches_found": result["matches_found"],
                "matches": result["matches"][:50],
                "dedup": result["dedup"],
                "pnl": result["pnl"],
                "issues": result["issues"],
                "analysis_run_id": run_id,
                "quote_currency": quote_currency.upper(),
                "use_ptax": bool(use_ptax),
                "income_events": result.get("income_events", {}),
                "loss_harvesting": result.get("loss_harvesting", {}),
                "monthly_sales_brl": result.get("monthly_sales_brl", {}),
                "isencao_threshold_brl": result.get("isencao_threshold_brl", 35000.0),
                "darf": result.get("darf"),
                "offshore_onshore": result.get("offshore_onshore", {}),
                "tax_savings_opportunities": result.get("tax_savings_opportunities", []),
                "p2p_self_custody_count": result.get("p2p_self_custody_count", 0),
            }
        )
    finally:
        for path in tmp_paths:
            try:
                os.unlink(path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Async Analysis (Background Task + SSE)
# ---------------------------------------------------------------------------

@router.post("/analyze-upload-async")
async def analyze_upload_async(
    file: UploadFile = File(...),
    format: str = Form("native"),
    accounting_method: str = Form("FIFO"),
    max_amount_diff: float = Form(0.01),
    max_time_diff_seconds: int = Form(3600),
    country: str = Form("br"),
    quote_currency: str = Form("BRL"),
    use_ptax: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Submit analysis as a background task. Returns task_id immediately.
    
    Monitor progress via:
      - SSE: GET /v1/sse/task/{task_id}
      - Polling: GET /v1/task/{task_id}
    """
    from app.services.task_manager import TaskManager
    from app.core.tasks import enqueue_analysis
    from app.services.analysis_service import check_transaction_limit

    manager = TaskManager()
    task_id = manager.create_task()

    file_bytes = await file.read()
    
    # Enforce transaction limits based on subscription plan
    check_transaction_limit(db, current_user.id, file_bytes)

    filename = file.filename or "upload.csv"
    user_id = current_user.id

    # Enqueue task to Arq worker
    await enqueue_analysis(
        task_id,
        file_bytes,
        user_id,
        filename,
        format_name=format,
        accounting_method=accounting_method,
        country=country,
        quote_currency=quote_currency,
        use_ptax=use_ptax,
        max_amount_diff=max_amount_diff,
        max_time_diff_seconds=max_time_diff_seconds,
    )

    return {
        "task_id": task_id,
        "status": "submitted",
        "sse_url": f"/v1/sse/task/{task_id}",
        "poll_url": f"/v1/task/{task_id}",
    }


@router.get("/task/{task_id}")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Poll task status (fallback when SSE is unavailable)."""
    from app.services.stream_transport import TaskStore

    store = TaskStore.get()
    status = store.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return status.to_dict()

@router.get("/br/analysis/latest")
def get_latest_analysis(
    tax_year: int | None = Query(default=None, ge=1900, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _cached_dashboard_analysis(db, current_user.id, tax_year)


@router.post("/br/analysis/from-sources", response_model=AnalysisResultResponse)
def analyze_selected_sources(
    payload: SourceAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    raw = _selected_sources_df(db, current_user, payload.source_ids)
    country = (payload.country or "br").lower()
    quote_currency = COUNTRY_QUOTE_CURRENCY.get(country, "USD")

    result = analyze_from_dataframe(
        raw,
        format_name="native",
        accounting_method=payload.accounting_method,
        country=country,
        quote_currency=quote_currency,
        use_ptax=payload.use_ptax,
        max_amount_diff=0.01,
        max_time_diff_seconds=3600,
        source_provider="selected_sources",
    )

    run_id = persist_run(
        db,
        current_user.id,
        result["normalized"],
        {
            "pnl": result["pnl"],
            "rows_processed": result["rows_processed"],
            "matches_found": result["matches_found"],
            "format": "selected_sources",
            "quote_currency": quote_currency,
            "accounting_method": payload.accounting_method,
            "use_ptax": bool(payload.use_ptax),
            "selected_source_ids": payload.source_ids,
            "auto_classify": bool(payload.auto_classify),
        },
    )

    updated_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    run_summary = json.loads(updated_run.summary_json or "{}") if updated_run else {}

    return AnalysisResultResponse.model_validate(
        {
            "status": "ok",
            "filename": "selected_sources",
            "rows_processed": result["rows_processed"],
            "matches_found": result["matches_found"],
            "analysis_run_id": run_id,
            "lot_matches": result["pnl"].get("lot_matches", [])[:100],
            "transfer_matches": result["matches"][:50],
            "dedup": result["dedup"],
            "pnl": result["pnl"],
            "issues": result["issues"],
            "quote_currency": quote_currency.upper(),
            "use_ptax": bool(payload.use_ptax),
            "income_events": result.get("income_events", {}),
            "loss_harvesting": result.get("loss_harvesting", {}),
            "monthly_sales_brl": result.get("monthly_sales_brl", {}),
            "isencao_threshold_brl": result.get("isencao_threshold_brl", 35000.0),
            "darf": result.get("darf"),
            "offshore_onshore": result.get("offshore_onshore", {}),
            "tax_savings_opportunities": result.get("tax_savings_opportunities", []),
            "p2p_self_custody_count": result.get("p2p_self_custody_count", 0),
            "tx_imported": run_summary.get("tx_imported", result["rows_processed"]),
            "tx_skipped": run_summary.get("tx_skipped", 0),
        }
    )
