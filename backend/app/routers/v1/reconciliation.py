"""Reconciliation API — detect and resolve transaction issues."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import AnalysisRun, User
from app.services.analysis_service import get_run
from app.services.reconciliation_service import ReconciliationEngine

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ResolveRequest(BaseModel):
    issue_id: int
    resolution: str = Field(..., description="PURCHASE | GIFT | AIRDROP | INTERNAL_TRANSFER | MINING | STAKING_REWARD | IGNORE")
    cost_basis_override: Optional[float] = None
    linked_wallet: Optional[str] = None
    linked_tx_index: Optional[int] = None


class BulkResolveRequest(BaseModel):
    issue_ids: list[int]
    resolution: str = Field(..., description="PURCHASE | GIFT | AIRDROP | INTERNAL_TRANSFER | MINING | STAKING_REWARD | IGNORE")
    cost_basis_override: Optional[float] = None


class IssueResponse(BaseModel):
    id: int
    run_id: int
    tx_index: int
    tx_hash: Optional[str] = None
    asset: Optional[str] = None
    amount: Optional[float] = None
    timestamp: Optional[str] = None
    issue_type: str
    severity: str
    description: Optional[str] = None
    suggested_matches: list[dict] = []
    resolved: bool = False
    resolved_as: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/issues/{run_id}")
def list_issues(
    run_id: int,
    resolved: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List all reconciliation issues for an analysis run."""
    # Verify run belongs to user
    get_run(db, current_user, run_id)

    engine = ReconciliationEngine(db)
    issues = engine.get_issues(run_id, current_user.id, resolved=resolved)
    stats = engine.get_stats(run_id, current_user.id)

    items = []
    for issue in issues:
        matches = []
        if issue.suggested_matches_json:
            try:
                matches = json.loads(issue.suggested_matches_json)
            except (json.JSONDecodeError, TypeError):
                matches = []

        items.append({
            "id": issue.id,
            "run_id": issue.run_id,
            "tx_index": issue.tx_index,
            "tx_hash": issue.tx_hash,
            "asset": issue.asset,
            "amount": float(issue.amount) if issue.amount else None,
            "timestamp": str(issue.timestamp) if issue.timestamp else None,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "description": issue.description,
            "suggested_matches": matches,
            "resolved": issue.resolved,
            "resolved_as": issue.resolved_as,
        })

    return {"issues": items, "stats": stats}


@router.post("/resolve")
def resolve_issue(
    payload: ResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve a reconciliation issue with the user's decision."""
    engine = ReconciliationEngine(db)

    try:
        issue = engine.resolve_issue(
            issue_id=payload.issue_id,
            user_id=current_user.id,
            resolution=payload.resolution,
            cost_basis_override=payload.cost_basis_override,
            linked_wallet=payload.linked_wallet,
            linked_tx_index=payload.linked_tx_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "resolved",
        "issue_id": issue.id,
        "resolved_as": issue.resolved_as,
    }


@router.post("/auto-match/{run_id}")
def trigger_auto_match(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Trigger cross-wallet auto-matching for all unresolved issues in a run.
    Searches buy orders across ALL user's loaded analysis runs.
    """
    _ = get_run(db, current_user, run_id)
    engine = ReconciliationEngine(db)

    # Get unresolved issues
    issues_db = engine.get_issues(run_id, current_user.id, resolved=False)
    if not issues_db:
        return {"status": "ok", "message": "No unresolved issues to match", "matched": 0}

    # Convert DB issues to DetectedIssue format for matching
    from app.services.reconciliation_service import DetectedIssue
    import pandas as pd

    detected = []
    for issue in issues_db:
        ts = None
        if issue.timestamp:
            try:
                ts = pd.to_datetime(issue.timestamp)
            except Exception:
                ts = None

        detected.append(DetectedIssue(
            tx_index=issue.tx_index,
            issue_type=issue.issue_type,
            severity=issue.severity,
            description=issue.description or "",
            asset=issue.asset,
            amount=float(issue.amount) if issue.amount else None,
            timestamp=ts,
            tx_hash=issue.tx_hash,
        ))

    # Load all user's runs for cross-matching
    all_runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == current_user.id)
        .all()
    )

    # Run auto-matching
    matched_issues = engine.auto_match_across_wallets(detected, all_runs, current_user.id)

    # Update DB with new suggestions
    matched_count = 0
    for det_issue, db_issue in zip(matched_issues, issues_db):
        if det_issue.suggested_matches:
            db_issue.suggested_matches_json = json.dumps(
                [m.to_dict() for m in det_issue.suggested_matches]
            )
            matched_count += 1

    db.commit()

    return {
        "status": "ok",
        "total_issues": len(issues_db),
        "matched": matched_count,
        "message": f"Found suggestions for {matched_count} issues across {len(all_runs)} runs.",
    }


@router.post("/scan/{run_id}")
def scan_run_for_issues(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Scan an analysis run for reconciliation issues."""
    run = get_run(db, current_user, run_id)

    # Load the normalized CSV
    from pathlib import Path
    import pandas as pd

    backend_root = Path(__file__).resolve().parents[3]
    csv_path = backend_root / run.csv_rel_path
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Analysis data not found on disk")

    normalized = pd.read_csv(str(csv_path))

    engine = ReconciliationEngine(db)

    # Check if already scanned — clear old issues first
    existing = engine.get_issues(run_id, current_user.id)
    if existing:
        for old in existing:
            if not old.resolved:
                db.delete(old)
        db.commit()

    # Scan
    issues = engine.scan_for_issues(normalized, run_id, current_user.id)

    # Auto-match across wallets
    all_runs = db.query(AnalysisRun).filter(AnalysisRun.user_id == current_user.id).all()
    issues = engine.auto_match_across_wallets(issues, all_runs, current_user.id)

    # Persist
    ids = engine.persist_issues(issues, run_id, current_user.id)
    stats = engine.get_stats(run_id, current_user.id)

    return {
        "status": "ok",
        "issues_found": len(ids),
        "stats": stats,
    }


@router.post("/bulk-resolve")
def bulk_resolve(
    payload: BulkResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve multiple reconciliation issues at once."""
    from app.scheduler import trigger_recalculation
    
    engine = ReconciliationEngine(db)
    resolved_count = 0
    
    # Use explicit transaction block for atomicity
    with db.begin():
        for issue_id in payload.issue_ids:
            try:
                engine.resolve_issue(
                    issue_id=issue_id,
                    user_id=current_user.id,
                    resolution=payload.resolution,
                    cost_basis_override=payload.cost_basis_override,
                )
                resolved_count += 1
            except ValueError:
                # If one fails (e.g. not found or not owned), the whole transaction will rollback
                # due to the 'with db.begin()' block if an exception is raised out of it.
                # However, resolve_issue might have internal checks.
                raise HTTPException(status_code=400, detail=f"Failed to resolve issue {issue_id}")

    # Trigger background recalculation
    trigger_recalculation(current_user.id)

    return {
        "status": "resolved",
        "count": resolved_count,
        "resolution": payload.resolution,
        "recalculation_triggered": True,
    }


# ---------------------------------------------------------------------------
# Custom Tags — User-defined transaction classification
# ---------------------------------------------------------------------------

VALID_TAGS = {
    "gift":     "Gift received — income at market price",
    "donation": "Donation received — income at market price",
    "personal": "Personal transfer — not taxable",
    "lost":     "Lost funds — removed from inventory",
    "stolen":   "Stolen funds — removed from inventory",
    "payment":  "Payment for goods/services — income",
    "salary":   "Salary/compensation — income",
    "fork":     "Hard fork — zero cost basis (or income, per jurisdiction)",
    "mining":   "Mining reward — income at market price",
    "ignore":   "Ignore — excluded from tax calculations entirely",
}


class TagRequest(BaseModel):
    tag: Optional[str] = Field(None, description="Tag to set, or null to remove")


@router.get("/transactions/tags")
def list_available_tags(
    current_user: User = Depends(get_current_user),
):
    """List all available custom tags with descriptions."""
    return {
        "tags": [
            {"value": k, "label": k.title(), "description": v}
            for k, v in VALID_TAGS.items()
        ]
    }


@router.patch("/transactions/{transaction_id}/tag")
def set_transaction_tag(
    transaction_id: int,
    payload: TagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set or remove a custom tag on a transaction.

    Custom tags override automatic type classification for tax calculations.
    Set tag=null to remove the override.
    """
    from app.models.transaction import Transaction

    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.tag is not None:
        tag = payload.tag.lower().strip()
        if tag not in VALID_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag '{tag}'. Valid tags: {list(VALID_TAGS.keys())}",
            )
        tx.custom_tag = tag
    else:
        tx.custom_tag = None

    db.commit()

    return {
        "transaction_id": transaction_id,
        "custom_tag": tx.custom_tag,
        "effect": VALID_TAGS.get(tx.custom_tag, "Default — automatic classification"),
        "note": "Re-run analysis to apply the new tag to tax calculations.",
    }
