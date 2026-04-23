from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import AnalysisRun, User
from app.pipeline.defi_pipeline import generate_defi_audit_report
from app.schemas.defi import DeFiProtocolInfo, DefiClassifyRequest, DefiClassifyResponse

router = APIRouter(tags=["defi"])
BACKEND_ROOT = Path(__file__).resolve().parents[3]


@router.get("/br/defi/protocols")
def list_defi_protocols() -> dict[str, DeFiProtocolInfo]:
    from app.integrations.defi_recognizer import get_supported_protocols

    return {
        key: DeFiProtocolInfo(**value)
        for key, value in get_supported_protocols().items()
    }


@router.get("/br/defi/protocols/{protocol_name}")
def get_defi_protocol(protocol_name: str) -> dict[str, object]:
    from app.integrations.defi_recognizer import get_supported_protocols

    protocols = get_supported_protocols()
    if protocol_name not in protocols:
        raise HTTPException(
            status_code=404,
            detail=f"Protocol '{protocol_name}' not found. Available: {', '.join(protocols.keys())}",
        )
    return protocols[protocol_name]


@router.post("/br/defi/classify", response_model=DefiClassifyResponse)
def classify_defi_transactions(
    body: DefiClassifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DefiClassifyResponse:
    from app.pipeline.defi_pipeline import (
        enrich_transactions_with_defi,
        generate_defi_audit_report,
        get_defi_summary_statistics,
    )

    if not body.transactions:
        return DefiClassifyResponse(
            total_transactions=0,
            defi_transactions=0,
            classified_transactions=[],
            summary_statistics={},
            audit_report={},
        )

    try:
        df = pd.DataFrame(body.transactions)
        for col in ["timestamp", "asset", "type", "amount"]:
            if col not in df.columns:
                df[col] = None
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse transaction data: {exc}") from exc

    try:
        classified_df = enrich_transactions_with_defi(df)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DeFi classification failed: {exc}") from exc

    defi_df = classified_df[classified_df["defi_protocol"].notna()]
    return DefiClassifyResponse(
        total_transactions=len(df),
        defi_transactions=len(defi_df),
        classified_transactions=defi_df.to_dict(orient="records"),
        summary_statistics=get_defi_summary_statistics(classified_df),
        audit_report=generate_defi_audit_report(classified_df),
    )


def _get_run_csv(db: Session, user: User, analysis_run_id: int) -> pd.DataFrame:
    analysis_run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == analysis_run_id, AnalysisRun.user_id == user.id)
        .first()
    )
    if not analysis_run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    csv_path = Path(analysis_run.csv_rel_path)
    if not csv_path.is_absolute():
        csv_path = BACKEND_ROOT / csv_path
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Analysis run data not found")
    try:
        return pd.read_csv(str(csv_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read analysis data: {exc}") from exc


@router.post("/br/defi/audit/{analysis_run_id}")
def defi_audit_report(
    analysis_run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        df = _get_run_csv(db, current_user, analysis_run_id)
        return generate_defi_audit_report(df)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit report generation failed: {exc}") from exc


@router.get("/br/defi/stats/{analysis_run_id}")
def defi_stats(
    analysis_run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    from app.pipeline.defi_pipeline import (
        calculate_farming_metrics,
        calculate_lp_metrics,
        enrich_transactions_with_defi,
        get_defi_summary_statistics,
    )

    try:
        df = enrich_transactions_with_defi(_get_run_csv(db, current_user, analysis_run_id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "summary": get_defi_summary_statistics(df),
        "lp_metrics": calculate_lp_metrics(df),
        "farming_metrics": calculate_farming_metrics(df),
    }
