"""
Tests for TLH API endpoints
Unit and integration tests
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.server import create_app
from app.core.db import Base, get_db
from app.models import (
    TLHOpportunity,
    TLHExecutionHistory,
    RecommendationStatus,
    ExecutionStrategy,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    async with TestingSessionLocal() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client"""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_opportunity(test_db):
    """Create sample TLH opportunity"""
    opp = TLHOpportunity(
        id="test_opp_1",
        user_id="test_user",
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
    test_db.add(opp)
    await test_db.commit()
    await test_db.refresh(opp)
    return opp


# ============================================================================
# SCAN ENDPOINT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_scan_portfolio_no_opportunities(client, test_db):
    """Test scanning empty portfolio"""
    response = await client.post("/api/v1/tlh/scan")
    assert response.status_code == 200
    data = response.json()
    assert data["opportunities_found"] == 0
    assert data["total_harvestable_losses"] == "0"


@pytest.mark.asyncio
async def test_scan_portfolio_with_opportunities(client, test_db, sample_opportunity):
    """Test scanning portfolio with opportunities"""
    response = await client.post("/api/v1/tlh/scan")
    assert response.status_code == 200
    data = response.json()
    assert data["opportunities_found"] == 1
    assert len(data["opportunities"]) == 1
    assert data["opportunities"][0]["asset"] == "BTC"


# ============================================================================
# LIST OPPORTUNITIES TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_opportunities_empty(client, test_db):
    """Test listing opportunities when none exist"""
    response = await client.get("/api/v1/tlh/opportunities")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_opportunities_with_filter(client, test_db, sample_opportunity):
    """Test listing opportunities with asset filter"""
    response = await client.get("/api/v1/tlh/opportunities?asset=BTC")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset"] == "BTC"


@pytest.mark.asyncio
async def test_list_opportunities_asset_filter_no_match(client, test_db, sample_opportunity):
    """Test asset filter with no matches"""
    response = await client.get("/api/v1/tlh/opportunities?asset=ETH")
    assert response.status_code == 200
    assert response.json() == []


# ============================================================================
# GET OPPORTUNITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_opportunity(client, test_db, sample_opportunity):
    """Test getting specific opportunity"""
    response = await client.get(f"/api/v1/tlh/opportunities/{sample_opportunity.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_opportunity.id
    assert data["asset"] == "BTC"
    assert data["priority_score"] == 85.5


@pytest.mark.asyncio
async def test_get_opportunity_not_found(client, test_db):
    """Test getting non-existent opportunity"""
    response = await client.get("/api/v1/tlh/opportunities/nonexistent")
    assert response.status_code == 404


# ============================================================================
# CREATE OPPORTUNITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_opportunity(client, test_db):
    """Test creating new opportunity"""
    payload = {
        "position_id": "pos_new",
        "asset": "ETH",
        "loss_amount": "1.5",
        "tax_rate": 24.0,
        "priority_score": 72.5,
        "explanation": "ETH showing loss",
    }
    response = await client.post("/api/v1/tlh/opportunities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "ETH"
    assert data["status"] == "new"


# ============================================================================
# UPDATE OPPORTUNITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_opportunity_status(client, test_db, sample_opportunity):
    """Test updating opportunity status"""
    payload = {
        "status": "approved",
        "notes": "Ready to execute",
    }
    response = await client.put(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["notes"] == "Ready to execute"


@pytest.mark.asyncio
async def test_update_nonexistent_opportunity(client, test_db):
    """Test updating non-existent opportunity"""
    payload = {"status": "approved"}
    response = await client.put("/api/v1/tlh/opportunities/nonexistent", json=payload)
    assert response.status_code == 404


# ============================================================================
# DELETE OPPORTUNITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_opportunity(client, test_db, sample_opportunity):
    """Test deleting opportunity"""
    response = await client.delete(f"/api/v1/tlh/opportunities/{sample_opportunity.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    
    # Verify it's marked as cancelled
    response = await client.get(f"/api/v1/tlh/opportunities/{sample_opportunity.id}")
    assert response.json()["status"] == "cancelled"


# ============================================================================
# EXECUTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_execute_opportunity_dry_run(client, test_db, sample_opportunity):
    """Test dry-run execution"""
    payload = {
        "strategy": "immediate",
        "dry_run": True,
    }
    response = await client.post(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}/execute",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["dry_run"] == True
    assert data["status"] == "dry_run_pending"


@pytest.mark.asyncio
async def test_execute_with_invalid_strategy(client, test_db, sample_opportunity):
    """Test execution with invalid strategy"""
    payload = {
        "strategy": "invalid_strategy",
        "dry_run": True,
    }
    response = await client.post(
        f"/api/v1/tlh/opportunities/{sample_opportunity.id}/execute",
        json=payload
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_execute_nonexistent_opportunity(client, test_db):
    """Test executing non-existent opportunity"""
    payload = {
        "strategy": "immediate",
        "dry_run": True,
    }
    response = await client.post(
        "/api/v1/tlh/opportunities/nonexistent/execute",
        json=payload
    )
    assert response.status_code == 404


# ============================================================================
# BULK EXECUTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_bulk_execute(client, test_db, sample_opportunity):
    """Test bulk execution"""
    # Create another opportunity
    opp2 = TLHOpportunity(
        id="test_opp_2",
        user_id="test_user",
        position_id="pos_2",
        asset="ETH",
        loss_amount=Decimal("2.0"),
        tax_rate=24.0,
        priority_score=78.0,
        status=RecommendationStatus.NEW.value,
    )
    test_db.add(opp2)
    await test_db.commit()
    
    payload = {
        "opportunity_ids": ["test_opp_1", "test_opp_2"],
        "strategy": "immediate",
        "dry_run": True,
    }
    response = await client.post("/api/v1/tlh/bulk-execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_opportunities"] == 2
    assert len(data["results"]) == 2


# ============================================================================
# EXECUTION HISTORY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_execution_history(client, test_db, sample_opportunity):
    """Test getting execution history"""
    # Create execution
    execution = TLHExecutionHistory(
        id="exec_1",
        opportunity_id=sample_opportunity.id,
        strategy="immediate",
        status="completed",
        dry_run=False,
        quantity_executed=Decimal("0.5"),
        average_price=Decimal("20000"),
    )
    test_db.add(execution)
    await test_db.commit()
    
    response = await client.get(f"/api/v1/tlh/opportunities/{sample_opportunity.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["strategy"] == "immediate"


# ============================================================================
# METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_metrics_empty(client, test_db):
    """Test metrics with no opportunities"""
    response = await client.get("/api/v1/tlh/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_harvestable_losses"] == "0"
    assert data["total_tax_benefit"] == "0"


@pytest.mark.asyncio
async def test_get_metrics_with_data(client, test_db, sample_opportunity):
    """Test metrics with opportunities"""
    response = await client.get("/api/v1/tlh/metrics")
    assert response.status_code == 200
    data = response.json()
    assert float(data["total_harvestable_losses"]) > 0
    assert float(data["total_tax_benefit"]) > 0


# ============================================================================
# HEALTH CHECK
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/api/v1/tlh/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "tlh"
