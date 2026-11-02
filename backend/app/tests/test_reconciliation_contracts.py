"""Issue detection, cross-wallet candidates and user-scoped resolutions."""
from datetime import datetime
from types import SimpleNamespace

import pandas as pd
import pytest

from app.models import AnalysisRun
from app.services.reconciliation_service import ReconciliationEngine, DetectedIssue
from app.tests.test_service_workflows import store


def test_detector_distinguishes_orphan_airdrop_and_known_transfer():
    engine = ReconciliationEngine(None)
    frame = pd.DataFrame([
        {"type": "RECEIVE", "asset": "BTC", "amount": 2, "price": None},
        {"type": "RECEIVE", "asset": "ETH", "amount": 0.1, "price": 0},
        {"type": "TRANSFER", "asset": "SOL", "amount": 3, "price": 10},
        {"type": "RECEIVE", "asset": "SOL", "amount": 3, "price": 10},
    ])
    issues = engine.scan_for_issues(frame, 1, 1)
    assert {i.issue_type for i in issues if i.tx_index == 0} == {"MISSING_COST_BASIS", "ORPHAN_RECEIVE"}
    assert {i.issue_type for i in issues if i.tx_index == 1} == {"MISSING_COST_BASIS", "POSSIBLE_AIRDROP"}
    assert not [i for i in issues if i.tx_index == 3]


def test_candidates_require_matching_amount_and_time_window(tmp_path):
    engine = ReconciliationEngine(None)
    issue = DetectedIssue(0, "ORPHAN_RECEIVE", "warning", "Unknown origin", asset="BTC", amount=1, timestamp=datetime(2025, 1, 2))
    frame = pd.DataFrame([
        {"asset": "BTC", "type": "TRANSFER", "amount": 1, "timestamp": "2025-01-02", "from_wallet": "my-wallet"},
        {"asset": "BTC", "type": "TRANSFER", "amount": 1, "timestamp": "2024-01-01", "from_wallet": "old"},
        {"asset": "BTC", "type": "BUY", "amount": 9, "timestamp": "2025-01-02", "from_wallet": "other"},
    ])
    file = tmp_path / "transactions.csv"
    frame.to_csv(file, index=False)
    result = engine.auto_match_across_wallets([issue], [SimpleNamespace(id=7, csv_rel_path=str(file))], 1)
    matches = result[0].suggested_matches
    assert len(matches) == 1
    assert matches[0].confidence == 1
    assert matches[0].to_dict()["wallet"] == "my-wallet"


def test_issue_persistence_resolution_and_user_isolation(store):
    db, user, other = store
    run = AnalysisRun(user_id=user.id, csv_rel_path="unused.csv", summary_json="{}")
    db.add(run)
    db.commit()
    engine = ReconciliationEngine(db)
    ids = engine.persist_issues([DetectedIssue(0, "MISSING_COST_BASIS", "error", "No basis", asset="BTC", amount=1)], run.id, user.id)
    assert engine.get_stats(run.id, user.id)["unresolved"] == 1
    assert engine.get_issues(run.id, other.id) == []
    with pytest.raises(ValueError):
        engine.resolve_issue(ids[0], other.id, "PURCHASE")
    with pytest.raises(ValueError):
        engine.resolve_issue(ids[0], user.id, "INVALID")
    resolved = engine.resolve_issue(ids[0], user.id, "PURCHASE", cost_basis_override=100)
    assert resolved.cost_basis_override == 100
    assert engine.get_stats(run.id, user.id)["progress_pct"] == 100
    assert engine.get_issues(run.id, user.id, resolved=False) == []
