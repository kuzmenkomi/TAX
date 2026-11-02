"""Persistence, ownership and audit history in the standalone tax engine."""
from datetime import datetime
from decimal import Decimal as D

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.advanced_tax.integration.database import Base
from app.advanced_tax.models.audit_models import VerifiedTaxRule, CalculationAuditRecord
from app.advanced_tax.models.reconciliation_models import MissingCostBasis, ReconciliationHistory
from app.advanced_tax.models.tax_loss_models import TaxLossHarvest, HarvestAction
from app.advanced_tax.services.audit_engine import AuditEngine
from app.advanced_tax.services.reconciliation import SmartReconciliationEngine
from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
from app.advanced_tax.utils import ServiceException


@pytest.fixture
def standalone_db():
    # This optional engine has its own metadata and references the legacy user table.
    if "user" not in Base.metadata.tables:
        sa.Table("user", Base.metadata, sa.Column("id", sa.Integer, primary_key=True))
    engine = sa.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.execute(Base.metadata.tables["user"].insert(), [{"id": 1}, {"id": 2}])
        db.commit()
        yield db
    engine.dispose()


def test_manual_cost_basis_updates_one_users_gap_and_records_history(standalone_db):
    db = standalone_db
    engine = SmartReconciliationEngine(db, 1, "US")
    assert engine.manual_entry(10, D("125"), notes="Purchase receipt")["cost_basis"] == 125
    assert engine.manual_entry(10, D("150"), source="receipt")["cost_basis"] == 150
    assert db.query(MissingCostBasis).count() == 1
    assert db.query(ReconciliationHistory).count() == 2
    assert SmartReconciliationEngine(db, 2, "US").get_reconciliation_summary()["total_gaps"] == 0
    result = engine.accept_match(10, 9)
    assert result["status"] == "success"
    gap = db.query(MissingCostBasis).one()
    assert gap.matched_transaction_id == 9
    assert engine.get_reconciliation_summary()["matched_count"] == 1
    assert gap.to_dict()["cost_basis"] == D("150")


@pytest.mark.parametrize("invalid", [0, -1, "10"])
def test_reconciliation_rejects_invalid_transaction_ids(standalone_db, invalid):
    with pytest.raises(ServiceException):
        SmartReconciliationEngine(standalone_db, 1).validate_inputs(transaction_id=invalid)


def test_reconciliation_empty_scan_and_no_suggestions(standalone_db):
    engine = SmartReconciliationEngine(standalone_db, 1)
    assert engine.scan_for_gaps() == []
    assert engine.find_matching_transactions(1) == []
    assert engine.get_reconciliation_summary()["total_tax_impact"] == 0


def test_verified_rule_lookup_and_calculation_ownership(standalone_db):
    db = standalone_db
    now = datetime(2025, 6, 1)
    rule = VerifiedTaxRule(rule_code="DEMO_CG", rule_name="Demo capital gains rule", country="US", tax_type="CG",
        rule_definition="{}", law_reference="Demo only", tax_authority="Demo", verified_by_user_id=1,
        verified_date=now, effective_date=now, last_reviewed=now, next_review_date=now)
    db.add(rule)
    db.flush()
    record = CalculationAuditRecord(user_id=1, asset="BTC", quantity=D("1"), buy_price=D("100"), sell_price=D("200"),
        tax_type="CG", tax_rate=D("0.15"), calculated_tax=D("15"), applied_rule_id=rule.id,
        reasoning="Demo arithmetic", calculation_method="FIFO", country="US", created_at=now)
    db.add(record)
    db.commit()
    audit = AuditEngine(db, 1, "US")
    assert audit.get_verified_rules()[0]["code"] == "DEMO_CG"
    assert audit.get_calculation_details(record.id)["calculation"]["calculated_tax"] == 15
    assert audit._get_tax_calculations(2025) == [record]
    assert audit._get_tax_calculations(2024) == []
    assert audit._get_rules_used([record]) == [rule]
    assert audit._get_rules_used([]) == []
    with pytest.raises(ServiceException):
        AuditEngine(db, 2, "US").get_calculation_details(record.id)
    original = audit._calculate_content_hash([], [record], [rule])
    assert len(original) == 64
    assert original != audit._calculate_content_hash([], [], [])


def test_harvest_persistence_and_execution_stay_user_scoped(standalone_db):
    db = standalone_db
    engine = TaxLossOptimizer(db, 1, "US")
    from app.advanced_tax.services.cost_basis_calculator import CostBasisLot
    opportunity = engine._evaluate_asset_for_harvest("BTC", {"last_price": 30000, "quantity": 1,
        "cost_basis_lots": [CostBasisLot("BTC", D("1"), D("40000"), datetime(2024, 1, 1))]})
    engine._save_opportunities([opportunity])
    saved = db.query(TaxLossHarvest).one()
    assert saved.net_tax_benefit() == D("2370")
    assert engine.get_tax_impact_summary()["total_opportunities"] == 1
    with pytest.raises(ServiceException, match="not found"):
        TaxLossOptimizer(db, 2, "US").execute_harvest(saved.id)
    result = engine.execute_harvest(saved.id)
    assert result["status"] == "executed"
    action = db.query(HarvestAction).one()
    assert action.asset == "BTC" and action.price == D("30000")
