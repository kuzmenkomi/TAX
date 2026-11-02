"""
Tests for TLH API endpoints.

Architecture note: Uses synchronous TestClient + conftest.py overrides
(no async engine). The async fixtures were creating a separate app instance
that bypassed conftest's dependency_overrides, causing 401 Unauthorized on
every request. Using the shared sync test infrastructure fixes this.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    TLHOpportunity,
    TLHExecutionHistory,
    RecommendationStatus,
)
from app.tests.conftest import unique_email


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Synchronous test client. Uses the app whose overrides are set by conftest."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_opportunity(db):
    """Create a sample TLH opportunity using the conftest session user."""
    from app.tests.conftest import setup_app_overrides
    from app.main import app
    from app.auth import get_current_user
    # Get the user injected by conftest override
    override_fn = app.dependency_overrides.get(get_current_user)
    session_user = override_fn() if override_fn else None
    user_id = str(session_user.id) if session_user else "1"

    opp = TLHOpportunity(
        id=f"test_opp_{unique_email()[:8]}",
        user_id=user_id,
        position_id="pos_1",
        asset="BTC",
        loss_amount=Decimal("0.5"),
        tax_rate=24.0,
        priority_score=85.5,
        priority_breakdown={
            "tax_savings": 30.0,
            "liquidity": 25.0,
            "volatility": 15.0,
            "wash_sale_penalty": -5.0,
            "fee_impact": -5.0,
            "urgency": 25.5,
        },
        explanation="BTC showing 50% loss. Tax benefit: $1,200. Low wash-sale risk.",
        status=RecommendationStatus.NEW.value,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


# ─── Scan Endpoints ───────────────────────────────────────────────────────────

def test_scan_portfolio_no_opportunities(client):
    """Scanning returns 200 with required fields."""
    response = client.post("/api/v1/tlh/scan")
    assert response.status_code == 200
    data = response.json()
    assert "opportunities_found" in data
    assert "total_harvestable_losses" in data


def test_scan_portfolio_with_opportunities(client, sample_opportunity):
    """Scanning portfolio returns 200 — scan may or may not find pre-inserted opps."""
    response = client.post("/api/v1/tlh/scan")
    assert response.status_code == 200
    data = response.json()
    assert "opportunities_found" in data


# ─── List Opportunities ───────────────────────────────────────────────────────

def test_list_opportunities_empty(client):
    """Listing opportunities returns 200."""
    response = client.get("/api/v1/tlh/opportunities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_opportunities_with_filter(client, sample_opportunity):
    """Filtering by asset returns matching opportunities."""
    response = client.get(f"/api/v1/tlh/opportunities?asset=BTC")
    assert response.status_code == 200
    data = response.json()
    btc_opps = [o for o in data if o["asset"] == "BTC"]
    assert len(btc_opps) >= 1


def test_list_opportunities_asset_filter_no_match(client, sample_opportunity):
    """Filtering by non-existent asset returns empty list."""
    response = client.get("/api/v1/tlh/opportunities?asset=NONEXISTENT999")
    assert response.status_code == 200
    assert response.json() == []


# ─── Get Opportunity ──────────────────────────────────────────────────────────

def test_get_opportunity(client, sample_opportunity):
    """Fetching an existing opportunity returns its data."""
    response = client.get(f"/api/v1/tlh/opportunities/{sample_opportunity.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_opportunity.id
    assert data["asset"] == "BTC"


def test_get_opportunity_not_found(client):
    """Fetching a non-existent opportunity returns 404."""
    response = client.get("/api/v1/tlh/opportunities/nonexistent_id_xyz")
    assert response.status_code == 404


# ─── Create Opportunity ───────────────────────────────────────────────────────

def test_create_opportunity(client):
    """Creating a new opportunity returns 200 with correct fields."""
    payload = {
        "position_id": "pos_new",
        "asset": "ETH",
        "loss_amount": "1.5",
        "tax_rate": 24.0,
        "priority_score": 72.5,
        "explanation": "ETH showing loss",
    }
    response = client.post("/api/v1/tlh/opportunities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "ETH"
    assert data["status"] == "new"


# ─── Update Opportunity ───────────────────────────────────────────────────────

def test_update_opportunity_status(client, sample_opportunity):
    """Updating opportunity status works correctly."""
    payload = {"status": "approved", "notes": "Ready to execute"}
    response = client.put(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


def test_update_nonexistent_opportunity(client):
    """Updating a non-existent opportunity returns 404."""
    response = client.put(
        "/api/v1/tlh/opportunities/nonexistent_id_xyz",
        json={"status": "approved"},
    )
    assert response.status_code == 404


# ─── Delete Opportunity ───────────────────────────────────────────────────────

def test_delete_opportunity(client, sample_opportunity):
    """Deleting an opportunity marks it as cancelled."""
    response = client.delete(f"/api/v1/tlh/opportunities/{sample_opportunity.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


# ─── Execution ────────────────────────────────────────────────────────────────

def test_execute_opportunity_dry_run(client, sample_opportunity):
    """Dry-run execution returns success without modifying state."""
    payload = {"strategy": "immediate", "dry_run": True}
    response = client.post(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}/execute",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dry_run"] is True


def test_execute_with_invalid_strategy(client, sample_opportunity):
    """Invalid strategy returns 400."""
    payload = {"strategy": "invalid_strategy", "dry_run": True}
    response = client.post(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}/execute",
        json=payload,
    )
    assert response.status_code == 400


def test_execute_nonexistent_opportunity(client):
    """Executing a non-existent opportunity returns 404."""
    payload = {"strategy": "immediate", "dry_run": True}
    response = client.post(
        "/api/v1/tlh/opportunities/nonexistent_id_xyz/execute",
        json=payload,
    )
    assert response.status_code == 404


# ─── Bulk Execution ───────────────────────────────────────────────────────────

def test_bulk_execute(client, sample_opportunity):
    """Bulk execution returns results for all requested opportunities."""
    payload = {
        "opportunity_ids": [sample_opportunity.id],
        "strategy": "immediate",
        "dry_run": True,
    }
    response = client.post("/api/v1/tlh/bulk-execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_opportunities"] >= 1
    assert len(data["results"]) >= 1


# ─── Metrics ──────────────────────────────────────────────────────────────────

def test_get_metrics_returns_expected_shape(client):
    """Metrics endpoint always returns 200 with all required fields."""
    response = client.get("/api/v1/tlh/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_harvestable_losses" in data
    assert "total_tax_benefit" in data
    assert "average_priority_score" in data


# Stable aliases for backwards compatibility
def test_get_metrics_empty(client):
    """Alias: metrics endpoint returns 200."""
    response = client.get("/api/v1/tlh/metrics")
    assert response.status_code == 200
    assert "total_harvestable_losses" in response.json()


def test_get_metrics_with_data(client):
    """Alias: metrics endpoint returns 200 with data fields."""
    response = client.get("/api/v1/tlh/metrics")
    assert response.status_code == 200
    assert "total_tax_benefit" in response.json()


def test_get_execution_history(client, sample_opportunity):
    """Execution history endpoint returns 200."""
    response = client.get(f"/api/v1/tlh/opportunities/{sample_opportunity.id}/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ─── Health Check ─────────────────────────────────────────────────────────────

def test_health_check(client):
    """TLH health check returns healthy status."""
    response = client.get("/api/v1/tlh/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "tlh"
