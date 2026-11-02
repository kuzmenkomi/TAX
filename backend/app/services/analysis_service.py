from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AnalysisRun, ImportJob, User

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = BACKEND_ROOT / "data" / "runs"


def persist_run(
    db: Session,
    user_id: int,
    normalized: pd.DataFrame,
    summary: dict[str, Any],
    lot_matches: list[dict] | None = None,
    file_hash: str | None = None,
) -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = RUNS_DIR / f"run_{user_id}_{ts}.csv"
    normalized.to_csv(csv_path, index=False)
    csv_rel_path = str(csv_path.relative_to(BACKEND_ROOT)).replace("\\", "/")

    run = AnalysisRun(
        user_id=user_id,
        csv_rel_path=csv_rel_path,
        summary_json=json.dumps(summary, default=str),
        file_hash=file_hash,
    )
    db.add(run)
    db.commit()
    db.refresh(run)


    # Save transactions with row-level deduplication
    from app.services.transaction_service import save_transactions_from_df
    dedup_stats = save_transactions_from_df(db, user_id, run.id, normalized)
    summary["tx_imported"] = dedup_stats["imported"]
    summary["tx_skipped"] = dedup_stats["skipped"]
    # Update run summary with dedup stats
    run.summary_json = json.dumps(summary, default=str)
    db.commit()

    # Resolve and save lot matches from pnl (works for both FIFO/calculator and AVCO engines)
    pnl_data = summary.get("pnl", {})
    raw_lot_matches = pnl_data.get("lot_matches", []) if isinstance(pnl_data, dict) else []
    if raw_lot_matches:
        from app.models.transaction import Transaction as TxModel
        # Build external_id → db Transaction.id mapping for this run
        tx_rows = (
            db.query(TxModel.id, TxModel.external_id)
            .filter(TxModel.run_id == run.id, TxModel.user_id == user_id)
            .all()
        )
        ext_to_id: dict[str, int] = {row.external_id: row.id for row in tx_rows if row.external_id}
        # Resolve sell_tx_id and buy_tx_id using the mapping
        resolved = []
        for m in raw_lot_matches:
            m = dict(m)
            sell_ext = str(m.get("sell_tx_external_id") or "")
            buy_ext = str(m.get("buy_tx_external_id") or "")
            m["sell_tx_id"] = ext_to_id.get(sell_ext) or m.get("sell_tx_id")
            m["buy_tx_id"] = ext_to_id.get(buy_ext) or m.get("buy_tx_id")
            # Ensure required fields for LotMatch model exist
            if m.get("buy_timestamp") is None:
                m["buy_timestamp"] = m.get("sell_timestamp")
            resolved.append(m)
        # Persist resolved lot matches
        from app.models import User as UserModel
        user_obj = db.query(UserModel).get(user_id)
        if user_obj and resolved:
            from app.services.accounting_service import save_lot_matches
            save_lot_matches(db, user_obj, run.id, resolved)

    return run.id


def analyze_from_dataframe(
    raw: pd.DataFrame,
    *,
    format_name: str,
    accounting_method: str,
    country: str,
    quote_currency: str,
    use_ptax: bool,
    max_amount_diff: float,
    max_time_diff_seconds: int,
    source_provider: str | None = None,
) -> dict[str, Any]:
    from app.pipeline.analysis import run_tax_pipeline

    return run_tax_pipeline(
        raw,
        format_name=format_name,
        accounting_method=accounting_method,
        country=country,
        max_amount_diff=max_amount_diff,
        max_time_diff_seconds=max_time_diff_seconds,
        quote_currency=quote_currency,
        use_ptax=use_ptax,
        source_provider=source_provider if source_provider else (format_name if format_name != "native" else None),
        output_dir="output",
    )


def run_analysis_from_upload(
    db: Session,
    user: User,
    file_bytes: bytes,
    filename: str,
    *,
    format_name: str = "native",
    accounting_method: str = "FIFO",
    country: str = "br",
    quote_currency: str = "BRL",
    use_ptax: bool = False,
    max_amount_diff: float = 0.01,
    max_time_diff_seconds: int = 3600,
) -> dict[str, Any]:
    # Enforce transaction limits based on subscription plan
    check_transaction_limit(db, user.id, file_bytes)

    # ── Level 1: File-level deduplication via SHA-256 ──────────────────────
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    existing_run = None
    existing_job = (
        db.query(ImportJob)
        .filter(ImportJob.user_id == user.id, ImportJob.file_hash == file_hash)
        .first()
    )
    if existing_job:
        existing_run = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.user_id == user.id, AnalysisRun.file_hash == file_hash)
            .first()
        )
        if not existing_run:
            db.query(ImportJob).filter(
                ImportJob.user_id == user.id,
                ImportJob.file_hash == file_hash,
            ).delete(synchronize_session=False)
            db.commit()
    if existing_run:
        # Same file was already imported — find the existing run and return its summary
        existing_run = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.user_id == user.id, AnalysisRun.file_hash == file_hash)
            .first()
        )
        prev_summary: dict[str, Any] = {}
        if existing_run and existing_run.summary_json:
            try:
                prev_summary = json.loads(existing_run.summary_json)
            except Exception:
                pass
        return {
            "status": "duplicate",
            "duplicate": True,
            "filename": filename,
            "rows_processed": prev_summary.get("rows_processed", 0),
            "matches_found": prev_summary.get("matches_found", 0),
            "analysis_run_id": existing_run.id if existing_run else None,
            "lot_matches": [],
            "transfer_matches": [],
            "dedup": {"dropped": 0, "kept": 0},
            "pnl": prev_summary.get("pnl", {}),
            "issues": [],
            "quote_currency": quote_currency.upper(),
            "use_ptax": use_ptax,
            "income_events": {},
            "loss_harvesting": {},
            "monthly_sales_brl": {},
            "isencao_threshold_brl": 35000.0,
            "darf": None,
            "offshore_onshore": {},
            "tax_savings_opportunities": [],
            "p2p_self_custody_count": 0,
            "tx_imported": 0,
            "tx_skipped": prev_summary.get("rows_processed", 0),
        }

    # ── Level 2: Process file ───────────────────────────────────────────────
    from app.ingestion.csv_loader import load_csv
    suffix = Path(filename).suffix or ".csv"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        raw = load_csv(tmp_path, validate_native_schema=(format_name == "native"))

        if format_name != "native":
            from app.ingestion.registry import AdapterRegistry
            try:
                adapter = AdapterRegistry.get_adapter(format_name)
                raw = adapter.transform(raw)
            except ValueError:
                pass

        result = analyze_from_dataframe(
            raw,
            format_name="native",
            accounting_method=accounting_method,
            country=country,
            quote_currency=quote_currency,
            use_ptax=use_ptax,
            max_amount_diff=max_amount_diff,
            max_time_diff_seconds=max_time_diff_seconds,
            source_provider=format_name if format_name != "native" else None,
        )
    finally:
        os.unlink(tmp_path)

    # Save ImportJob with file hash
    job = ImportJob(
        user_id=user.id,
        source=format_name,
        filename=filename,
        file_hash=file_hash,
        status="done",
    )
    db.add(job)
    db.commit()

    run_id = persist_run(
        db,
        user.id,
        result["normalized"],
        {
            "pnl": result["pnl"],
            "rows_processed": result["rows_processed"],
            "matches_found": result["matches_found"],
            "format": format_name,
            "quote_currency": quote_currency,
            "accounting_method": accounting_method,
            "use_ptax": use_ptax,
        },
        file_hash=file_hash,
    )

    # Read back dedup stats from run summary
    updated_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    run_summary = json.loads(updated_run.summary_json or "{}") if updated_run else {}

    return {
        "status": "ok",
        "filename": filename,
        "rows_processed": result["rows_processed"],
        "matches_found": result["matches_found"],
        "analysis_run_id": run_id,
        "lot_matches": result["pnl"].get("lot_matches", [])[:100],
        "transfer_matches": result["matches"][:50],
        "dedup": result["dedup"],
        "pnl": result["pnl"],
        "issues": result["issues"],
        "quote_currency": quote_currency.upper(),
        "use_ptax": use_ptax,
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


def list_runs(db: Session, user: User, limit: int = 20, offset: int = 0) -> list[AnalysisRun]:
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == user.id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_run(db: Session, user: User, run_id: int) -> AnalysisRun:
    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == user.id,
    ).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    return run


def get_latest_analysis_result(db: Session, user_id: int) -> dict[str, Any] | None:
    """Helper to get the summary data from the most recent run."""
    latest = db.query(AnalysisRun).filter(AnalysisRun.user_id == user_id).order_by(AnalysisRun.created_at.desc()).first()
    if not latest:
        return None
    try:
        data = json.loads(latest.summary_json)
        data["analysis_run_id"] = latest.id
        return data
    except Exception:
        return None


def check_transaction_limit(db: Session, user_id: int, file_bytes: bytes):
    """Enforce plan transaction limit based on uploaded CSV row count."""
    from app.services.billing_service import get_user_plan, PLAN_LIMITS
    import io
    import pandas as pd

    plan = get_user_plan(db, user_id)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        row_count = len(df)
    except Exception:
        # If parsing fails here, let the load_csv step handle and raise standard validation errors
        return

    if row_count > limits["max_transactions"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "limit_exceeded",
                "message": f"Your plan ({plan.upper()}) is limited to {limits['max_transactions']} transactions, but this file contains {row_count} transactions. Please upgrade to process larger files.",
                "limit": limits["max_transactions"],
                "actual": row_count
            }
        )
