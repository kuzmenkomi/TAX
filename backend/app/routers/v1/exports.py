from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db, SessionLocal
from app.models import AnalysisRun, User
from app.services.report_service import ReportService
from app.services.plan_guard import require_paid_plan
from app.services.stream_transport import TaskStore, TaskStage
from app.services.export_task import generate_csv_export, generate_pdf_export
from app.services.billing_service import get_user_plan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exports", tags=["exports"])
BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _get_run(db: Session, user: User, run_id: int) -> AnalysisRun:
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == run_id, AnalysisRun.user_id == user.id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run


def _get_csv_path(run: AnalysisRun) -> Path:
    csv_path = Path(run.csv_rel_path)
    if not csv_path.is_absolute():
        csv_path = BACKEND_ROOT / csv_path
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Analysis run data not found")
    return csv_path


def _get_summary(run: AnalysisRun) -> dict:
    if not run.summary_json:
        return {}
    try:
        return json.loads(run.summary_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Analysis summary is invalid JSON") from exc


class ExportGenerateRequest(BaseModel):
    format: str  # "csv" or "pdf"
    run_id: int


def run_export_bg_task(task_id: str, format: str, run_id: int, user_id: int):
    """
    Generate CSV or PDF export and write to exports_cache directory.
    Uses database session factories to retrieve data.
    """
    db = SessionLocal()
    store = TaskStore.get()
    try:
        store.update(task_id, TaskStage.GENERATING_REPORTS, "Generating report...")
        user = db.query(User).filter(User.id == user_id).first()
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not user or not run:
            raise ValueError("User or analysis run not found")
            
        EXPORTS_DIR = BACKEND_ROOT / "exports_cache"
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        file_path = EXPORTS_DIR / f"{task_id}.{format.lower()}"
        
        if format.lower() == "csv":
            content_str = generate_csv_export(run, db)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_str)
        elif format.lower() == "pdf":
            content_bytes = generate_pdf_export(run, db, user)
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        store.update(task_id, TaskStage.COMPLETE, "Export generated successfully.")
    except Exception as e:
        logger.error(f"Error generating export in background: {e}", exc_info=True)
        store.update(task_id, TaskStage.FAILED, f"Export failed: {str(e)}", error=str(e))
    finally:
        db.close()


@router.get("/")
def get_exports():
    return {"message": "Exports API"}


@router.post("/generate")
async def generate_export(
    payload: ExportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan: str = Depends(require_paid_plan),
):
    run = _get_run(db, current_user, payload.run_id)
    csv_path = _get_csv_path(run)
    
    # Determine transaction count
    try:
        df = pd.read_csv(csv_path)
        row_count = len(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read transactions data: {str(e)}")
        
    store = TaskStore.get()
    task_id = store.create_task()
    
    if row_count < 500:
        # Run synchronously to be fast for small datasets
        run_export_bg_task(task_id, payload.format, payload.run_id, current_user.id)
        status = "completed"
    else:
        # Run asynchronously: Try worker first, fallback to BackgroundTasks
        status = "processing"
        try:
            from app.core.tasks import enqueue_export
            await enqueue_export(task_id, payload.format, payload.run_id, current_user.id)
        except Exception as e:
            logger.warning(f"Could not enqueue export task via arq/redis: {e}. Falling back to BackgroundTasks.")
            background_tasks.add_task(
                run_export_bg_task,
                task_id,
                payload.format,
                payload.run_id,
                current_user.id,
            )
            
    return {
        "task_id": task_id,
        "status": status,
        "row_count": row_count,
    }


@router.get("/status/{task_id}")
def get_export_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    store = TaskStore.get()
    progress = store.get_status(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Export task not found")
        
    if progress.stage == TaskStage.COMPLETE:
        status = "completed"
    elif progress.stage == TaskStage.FAILED:
        status = "failed"
    else:
        status = "processing"
        
    return {
        "task_id": task_id,
        "status": status,
        "progress": progress.progress,
        "message": progress.message,
        "error": progress.error,
    }


@router.get("/download/{task_id}")
def download_export(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    store = TaskStore.get()
    progress = store.get_status(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Export task not found or expired")
        
    if progress.stage != TaskStage.COMPLETE:
        raise HTTPException(status_code=400, detail="Export task is not complete yet")
        
    # Find generated file in exports_cache
    EXPORTS_DIR = BACKEND_ROOT / "exports_cache"
    
    # Try finding either .csv or .pdf file
    file_path = EXPORTS_DIR / f"{task_id}.csv"
    media_type = "text/csv"
    file_ext = "csv"
    
    if not file_path.exists():
        file_path = EXPORTS_DIR / f"{task_id}.pdf"
        media_type = "application/pdf"
        file_ext = "pdf"
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
        
    filename = f"declairo_export_{task_id}.{file_ext}"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/plan-check")
def plan_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.billing_service import PLAN_LIMITS
    plan = get_user_plan(db, current_user.id)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return {
        "can_export": plan != "free",
        "plan": plan,
        "upgrade_required": plan == "free",
        "max_transactions": limits["max_transactions"],
        "can_export_pdf": limits["can_export_pdf"],
    }


@router.get("/br/{run_id}")
def export_br_csv(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan: str = Depends(require_paid_plan),
):
    run = _get_run(db, current_user, run_id)
    csv_path = _get_csv_path(run)
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"declairo_run_{run_id}.csv",
    )


@router.get("/decripto/{run_id}")
def export_decripto_json(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan: str = Depends(require_paid_plan),
):
    run = _get_run(db, current_user, run_id)
    summary = _get_summary(run)
    payload = {
        "run_id": run.id,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "summary": summary,
    }
    return Response(
        content=json.dumps(payload, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="declairo_run_{run_id}.json"'},
    )


@router.get("/audit/{run_id}")
def export_audit_pdf(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan: str = Depends(require_paid_plan),
):
    run = _get_run(db, current_user, run_id)
    summary = _get_summary(run)
    return ReportService.generate_pdf_report(current_user, "br", datetime.utcnow().year, summary)


@router.get("/gcap/{run_id}")
def export_gcap_csv(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan: str = Depends(require_paid_plan),
):
    run = _get_run(db, current_user, run_id)
    csv_path = _get_csv_path(run)
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"gcap_source_run_{run_id}.csv",
    )
