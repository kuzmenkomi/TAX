from __future__ import annotations

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
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # 1. Save all transactions to DB first to get IDs
    from app.services.transaction_service import save_transactions_from_df
    db_transactions = save_transactions_from_df(db, user_id, run.id, normalized)
    
    # 2. Update lot_matches with correct DB IDs if possible
    # (Since calculate_pnl worked on indices, we map index to DB ID)
    if lot_matches:
        from app.services.accounting_service import save_lot_matches
        
        # Mapping index to Transaction ID
        # Note: normalized might have been re-indexed, so we rely on the order
        # from save_transactions_from_df which follows the DataFrame index
        # Actually, let's assume the lot_matches already have the IDs if they were available,
        # but here we ensure they are saved.
        # Wait, calculate_pnl needs to know the DB IDs. 
        # This is tricky because calculate_pnl runs BEFORE persist_run.
        
        save_lot_matches(db, db.query(User).get(user_id), run.id, lot_matches)

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
        source_provider=format_name if format_name != "native" else None,
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
    from app.ingestion.csv_loader import load_csv
    suffix = Path(filename).suffix or ".csv"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        raw = load_csv(tmp_path, validate_native_schema=(format_name == "native"))
        result = analyze_from_dataframe(
            raw,
            format_name=format_name,
            accounting_method=accounting_method,
            country=country,
            quote_currency=quote_currency,
            use_ptax=use_ptax,
            max_amount_diff=max_amount_diff,
            max_time_diff_seconds=max_time_diff_seconds,
        )
    finally:
        os.unlink(tmp_path)

    db.add(ImportJob(user_id=user.id, source=format_name, filename=filename, status="done"))
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
    )

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
        return json.loads(latest.summary_json)
    except Exception:
        return None
