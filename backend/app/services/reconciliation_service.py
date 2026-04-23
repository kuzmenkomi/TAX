"""
Reconciliation Service — Smart Transaction Issue Detection & Resolution.

Scans normalized transactions for issues like missing cost basis, orphan
receives (no matching send), and unknown sources. Provides cross-wallet
auto-matching and user-driven resolution workflows.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models import AnalysisRun, User
from app.models.reconciliation import ReconciliationIssue


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MatchCandidate:
    """A candidate match for an orphan transaction."""
    source_run_id: int
    tx_index: int
    asset: str
    amount: float
    timestamp: str
    wallet: str
    confidence: float  # 0..1
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_run_id": self.source_run_id,
            "tx_index": self.tx_index,
            "asset": self.asset,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "wallet": self.wallet,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
        }


@dataclass
class DetectedIssue:
    """An issue found during reconciliation scanning."""
    tx_index: int
    issue_type: str
    severity: str
    description: str
    asset: str | None = None
    amount: float | None = None
    timestamp: datetime | None = None
    tx_hash: str | None = None
    suggested_matches: list[MatchCandidate] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ISSUE_TYPES = {
    "MISSING_COST_BASIS": {
        "severity": "error",
        "desc": "Transaction has no cost basis / purchase price. Tax calculation may be inaccurate.",
    },
    "UNKNOWN_SOURCE": {
        "severity": "warning",
        "desc": "Received from an unknown address. Could be purchase, gift, airdrop, or internal transfer.",
    },
    "ORPHAN_RECEIVE": {
        "severity": "warning",
        "desc": "Received asset with no matching outgoing transfer in any loaded wallet.",
    },
    "POSSIBLE_INTERNAL_TRANSFER": {
        "severity": "info",
        "desc": "This looks like a transfer between your own wallets.",
    },
    "POSSIBLE_AIRDROP": {
        "severity": "info",
        "desc": "Small or free token receipt — likely an airdrop.",
    },
    "DUPLICATE_SUSPECT": {
        "severity": "warning",
        "desc": "This transaction may be a duplicate of another entry.",
    },
}

RESOLUTION_TYPES = [
    "PURCHASE",
    "GIFT",
    "AIRDROP",
    "INTERNAL_TRANSFER",
    "MINING",
    "STAKING_REWARD",
    "IGNORE",
]


# ---------------------------------------------------------------------------
# Reconciliation Engine
# ---------------------------------------------------------------------------

class ReconciliationEngine:
    """Scans transactions for issues and suggests resolutions."""

    def __init__(self, db: Session):
        self.db = db

    # ---- Scanning ----

    def scan_for_issues(
        self,
        normalized: pd.DataFrame,
        run_id: int,
        user_id: int,
    ) -> list[DetectedIssue]:
        """Scan a normalized DataFrame for reconciliation issues."""
        issues: list[DetectedIssue] = []

        for idx, row in normalized.iterrows():
            row_dict = row.to_dict()
            detected = self._check_row(int(idx), row_dict, normalized)
            issues.extend(detected)

        return issues

    def _check_row(
        self,
        idx: int,
        row: dict[str, Any],
        full_df: pd.DataFrame,
    ) -> list[DetectedIssue]:
        """Check a single row for issues."""
        found: list[DetectedIssue] = []
        tx_type = str(row.get("type", "")).upper()
        asset = row.get("asset", "")
        amount = float(row.get("amount", 0) or 0)
        price = row.get("price")
        ts = row.get("timestamp")
        tx_hash = row.get("external_id") or row.get("tx_hash") or ""

        # 1) Missing cost basis
        price_val = 0.0
        try:
            price_val = float(price) if price is not None else 0.0
        except (TypeError, ValueError):
            price_val = 0.0

        if tx_type in ("BUY", "SWAP", "TRADE", "RECEIVE") and price_val <= 0:
            found.append(DetectedIssue(
                tx_index=idx,
                issue_type="MISSING_COST_BASIS",
                severity="error",
                description=f"{asset}: No purchase price on {tx_type} of {amount:.6f} units.",
                asset=asset,
                amount=amount,
                timestamp=ts,
                tx_hash=str(tx_hash),
            ))

        # 2) Orphan receive (no matching TRANSFER in the same dataset)
        if tx_type == "RECEIVE":
            has_match = False
            transfers = full_df[full_df["type"].str.upper() == "TRANSFER"]
            for _, t_row in transfers.iterrows():
                if t_row.get("asset") != asset:
                    continue
                t_amount = float(t_row.get("amount", 0) or 0)
                if abs(t_amount - amount) / max(amount, 1e-8) < 0.05:  # within 5%
                    has_match = True
                    break

            if not has_match:
                # Heuristic: small amounts with zero-ish prices → possible airdrop
                if amount < 1.0 and price_val <= 0:
                    issue_type = "POSSIBLE_AIRDROP"
                else:
                    issue_type = "ORPHAN_RECEIVE"

                meta = ISSUE_TYPES[issue_type]
                found.append(DetectedIssue(
                    tx_index=idx,
                    issue_type=issue_type,
                    severity=meta["severity"],
                    description=f"{asset}: {meta['desc']} Amount: {amount:.6f}",
                    asset=asset,
                    amount=amount,
                    timestamp=ts,
                    tx_hash=str(tx_hash),
                ))

        return found

    # ---- Cross-wallet auto-matching ----

    def auto_match_across_wallets(
        self,
        issues: list[DetectedIssue],
        all_runs: list[AnalysisRun],
        user_id: int,
        *,
        time_tolerance_hours: int = 24,
        amount_tolerance_pct: float = 0.05,
    ) -> list[DetectedIssue]:
        """
        For each orphan issue, search all user's analysis runs for a matching
        BUY/TRANSFER that could explain the receive.
        """
        # Load all run DataFrames into memory
        run_dfs: dict[int, pd.DataFrame] = {}
        for run in all_runs:
            try:
                csv_path = run.csv_rel_path
                if csv_path:
                    from pathlib import Path
                    backend_root = Path(__file__).resolve().parents[2]
                    full_path = backend_root / csv_path
                    if full_path.exists():
                        run_dfs[run.id] = pd.read_csv(str(full_path))
            except Exception:
                continue

        for issue in issues:
            if issue.issue_type not in ("ORPHAN_RECEIVE", "UNKNOWN_SOURCE", "MISSING_COST_BASIS"):
                continue

            candidates: list[MatchCandidate] = []
            for rid, df in run_dfs.items():
                matches = self._find_candidates_in_df(
                    df, rid, issue,
                    time_tolerance_hours=time_tolerance_hours,
                    amount_tolerance_pct=amount_tolerance_pct,
                )
                candidates.extend(matches)

            # Sort by confidence descending
            candidates.sort(key=lambda c: c.confidence, reverse=True)
            issue.suggested_matches = candidates[:5]  # Top 5

        return issues

    def _find_candidates_in_df(
        self,
        df: pd.DataFrame,
        run_id: int,
        issue: DetectedIssue,
        *,
        time_tolerance_hours: int,
        amount_tolerance_pct: float,
    ) -> list[MatchCandidate]:
        """Search a DataFrame for transactions matching the issue."""
        candidates: list[MatchCandidate] = []

        if issue.asset is None or issue.amount is None:
            return candidates

        # Filter to matching asset
        asset_mask = df["asset"].str.upper() == issue.asset.upper()
        type_mask = df["type"].str.upper().isin(["BUY", "TRANSFER", "SWAP", "TRADE"])
        subset = df[asset_mask & type_mask]

        for idx, row in subset.iterrows():
            row_amount = float(row.get("amount", 0) or 0)
            if row_amount <= 0:
                continue

            # Amount proximity
            amt_diff_pct = abs(row_amount - issue.amount) / max(issue.amount, 1e-8)
            if amt_diff_pct > amount_tolerance_pct:
                continue

            # Time proximity
            confidence = 0.5
            reasons: list[str] = []

            try:
                row_ts = pd.to_datetime(row.get("timestamp"))
                if issue.timestamp is not None:
                    issue_ts = pd.to_datetime(issue.timestamp)
                    time_diff = abs((row_ts - issue_ts).total_seconds())
                    if time_diff <= time_tolerance_hours * 3600:
                        time_bonus = max(0, 1.0 - (time_diff / (time_tolerance_hours * 3600)))
                        confidence += 0.3 * time_bonus
                        reasons.append(f"Time diff: {time_diff / 3600:.1f}h")
                    else:
                        continue
            except Exception:
                pass

            # Amount match bonus
            if amt_diff_pct < 0.001:
                confidence += 0.2
                reasons.append("Exact amount match")
            elif amt_diff_pct < amount_tolerance_pct:
                confidence += 0.1
                reasons.append(f"Amount diff: {amt_diff_pct * 100:.2f}%")

            wallet = str(row.get("from_wallet", "") or row.get("to_wallet", "") or "")
            if wallet:
                reasons.append(f"Wallet: {wallet[:12]}...")

            candidates.append(MatchCandidate(
                source_run_id=run_id,
                tx_index=int(idx),
                asset=issue.asset,
                amount=row_amount,
                timestamp=str(row.get("timestamp", "")),
                wallet=wallet,
                confidence=min(confidence, 1.0),
                reason="; ".join(reasons),
            ))

        return candidates

    # ---- Persistence ----

    def persist_issues(
        self,
        issues: list[DetectedIssue],
        run_id: int,
        user_id: int,
    ) -> list[int]:
        """Save detected issues to the database. Returns list of issue IDs."""
        created_ids: list[int] = []

        for issue in issues:
            matches_json = None
            if issue.suggested_matches:
                matches_json = json.dumps([m.to_dict() for m in issue.suggested_matches])

            db_issue = ReconciliationIssue(
                user_id=user_id,
                run_id=run_id,
                tx_index=issue.tx_index,
                tx_hash=issue.tx_hash,
                asset=issue.asset,
                amount=issue.amount,
                timestamp=issue.timestamp,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                suggested_matches_json=matches_json,
                resolved=False,
            )
            self.db.add(db_issue)
            self.db.flush()
            created_ids.append(db_issue.id)

        self.db.commit()
        return created_ids

    def resolve_issue(
        self,
        issue_id: int,
        user_id: int,
        resolution: str,
        *,
        cost_basis_override: float | None = None,
        linked_wallet: str | None = None,
        linked_tx_index: int | None = None,
    ) -> ReconciliationIssue:
        """Resolve a reconciliation issue with user's decision."""
        issue = (
            self.db.query(ReconciliationIssue)
            .filter(
                ReconciliationIssue.id == issue_id,
                ReconciliationIssue.user_id == user_id,
            )
            .first()
        )
        if not issue:
            raise ValueError(f"Issue {issue_id} not found for user {user_id}")

        if resolution not in RESOLUTION_TYPES:
            raise ValueError(f"Invalid resolution: {resolution}. Must be one of {RESOLUTION_TYPES}")

        issue.resolved = True
        issue.resolved_as = resolution
        issue.resolved_at = datetime.now(timezone.utc)
        issue.resolved_by_user = True
        issue.cost_basis_override = cost_basis_override
        issue.linked_wallet = linked_wallet
        issue.linked_tx_index = linked_tx_index

        self.db.commit()
        self.db.refresh(issue)
        return issue

    def get_issues(
        self,
        run_id: int,
        user_id: int,
        *,
        resolved: bool | None = None,
    ) -> list[ReconciliationIssue]:
        """Get all issues for a run, optionally filtered by resolved status."""
        q = self.db.query(ReconciliationIssue).filter(
            ReconciliationIssue.run_id == run_id,
            ReconciliationIssue.user_id == user_id,
        )
        if resolved is not None:
            q = q.filter(ReconciliationIssue.resolved == resolved)
        return q.order_by(ReconciliationIssue.severity.desc(), ReconciliationIssue.id).all()

    def get_stats(self, run_id: int, user_id: int) -> dict[str, Any]:
        """Get issue statistics for a run."""
        all_issues = self.get_issues(run_id, user_id)
        total = len(all_issues)
        resolved_count = sum(1 for i in all_issues if i.resolved)
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for i in all_issues:
            by_type[i.issue_type] = by_type.get(i.issue_type, 0) + 1
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1

        return {
            "total": total,
            "resolved": resolved_count,
            "unresolved": total - resolved_count,
            "progress_pct": round(resolved_count / max(total, 1) * 100, 1),
            "by_type": by_type,
            "by_severity": by_severity,
        }
