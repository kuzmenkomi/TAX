from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import AnalysisRun, User
from app.phase10_integration import Phase10DataIntegration

router = APIRouter(tags=["phase10"])


def _get_run(db: Session, user: User, run_id: int) -> AnalysisRun:
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id, AnalysisRun.user_id == user.id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run


@router.post("/br/export/gcap")
def export_gcap(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.generate_gcap_report(current_user, _get_run(db, current_user, run_id), db)


@router.post("/br/export/carne-leao")
def export_carne_leao(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.generate_carne_leao_report(current_user, _get_run(db, current_user, run_id), db)


@router.post("/audit/export/csv")
def export_audit_csv(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.export_audit_trail_csv(current_user, _get_run(db, current_user, run_id), db)


@router.get("/audit/verify/{run_id}")
def verify_audit_trail(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_run(db, current_user, run_id)
    return Phase10DataIntegration.get_audit_verification_status(run_id, current_user, db)


@router.post("/tax-planning/scenarios/{position_id}")
def analyze_tax_scenarios(
    position_id: int,
    price_targets: list[float] | None = None,
    include_loss_harvest: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.analyze_tax_scenarios(
        position_id,
        price_targets,
        include_loss_harvest,
        current_user,
        db,
    )


@router.get("/tax-planning/income-optimization")
def analyze_income_optimization(
    staking_income: float = 0,
    airdrop_income: float = 0,
    lending_income: float = 0,
    current_user: User = Depends(get_current_user),
):
    total_income = staking_income + airdrop_income + lending_income
    return {
        "total_income": total_income,
        "total_estimated_tax": total_income * 0.35,
        "tax_rate": "35%",
        "breakdown": {
            "staking": staking_income,
            "airdrops": airdrop_income,
            "lending": lending_income,
        },
    }


@router.post("/ai/ask-question")
def ask_consultant(
    question: str,
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.ask_ai_question(question, run_id, current_user, db)


@router.get("/ai/presets")
def get_preset_questions():
    from app.tax.ai_consultant import PRESET_QUESTIONS

    return {"presets": [{"id": key, "question": value} for key, value in PRESET_QUESTIONS.items()]}


@router.post("/ai/opportunities")
def find_opportunities(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_run(db, current_user, run_id)
    return {
        "opportunities": [
            {
                "type": "long_term_holding",
                "savings": 5000,
                "description": "Hold positions 180+ days for 15% tax rate vs 35%",
            },
            {
                "type": "loss_harvesting",
                "savings": 2500,
                "description": "Use realized losses to offset gains",
            },
        ],
        "total_potential_savings": 7500.0,
        "recommended_priority_order": ["long_term_holding", "loss_harvesting"],
    }


@router.post("/sync/eigenlayer")
def sync_eigenlayer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.sync_eigenlayer_events(current_user, db)


@router.post("/sync/linea")
def sync_linea(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return Phase10DataIntegration.sync_linea_transactions(current_user, db)


@router.post("/analyze/multichain")
def analyze_multichain(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_run(db, current_user, run_id)
    return Phase10DataIntegration.analyze_multichain_taxes(current_user, db)


@router.post("/quality/analyze-issues")
def analyze_data_quality(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_run(db, current_user, run_id)
    return Phase10DataIntegration.get_quality_issues(run_id, current_user, db)


@router.post("/security/2fa/setup")
def setup_2fa(current_user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=503,
        detail="2FA setup is temporarily disabled until the full implementation is completed.",
    )
