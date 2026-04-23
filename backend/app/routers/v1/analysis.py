from __future__ import annotations

import json
import os
import tempfile

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.accounting.avco_engine import compute_pnl_avco
from app.accounting.price_fill import fill_missing_prices
from app.accounting.pricing import PriceService
from app.accounting.rp2_calculator import compute_pnl_with_rp2
from app.auth import get_current_user
from app.config.settings import load_config
from app.core.db import get_db
from app.ingestion.csv_loader import load_csv
from app.ingestion.registry import AdapterRegistry
from app.matching.service import match_transfers
from app.models import ImportJob, User
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


@router.get("/br/runs")
def read_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rows = list_runs(db, current_user, limit=50)
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
            }
        )
    return {"runs": runs}


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
        result = analyze_from_dataframe(
            combined,
            format_name=format,
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
    from app.core.db import SessionLocal
    import threading

    manager = TaskManager()
    task_id = manager.create_task()

    file_bytes = await file.read()
    filename = file.filename or "upload.csv"
    user_id = current_user.id

    def run_in_background():
        manager.run_analysis(
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
            db_factory=SessionLocal,
        )

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

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
