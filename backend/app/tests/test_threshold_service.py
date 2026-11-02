import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from app.services.threshold_service import ThresholdService
from app.models import Transaction

def test_brazil_threshold_under_limit():
    # Setup
    db = MagicMock()
    user_id = 1
    
    # Mock transactions (Domestic sale 25,000 BRL)
    tx1 = Transaction(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        tx_type="sell",
        asset="BTC",
        total_value=Decimal("25000.00"),
        from_wallet="MercadoBitcoin" # Domestic
    )
    
    # Mock database results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [tx1]
    db.execute.return_value = mock_result
    
    # Execute
    status = ThresholdService.get_monthly_status(db, user_id, "BR")
    
    # Verify
    assert status["current_domestic"] == 25000.0
    assert status["remaining"] == 10000.0
    assert status["percent"] == (25000 / 35000 * 100)
    assert "Atenção!" in status["advice"] or "Dica:" in status["advice"] or "isento" in status["advice"]

def test_brazil_threshold_over_limit():
    # Setup
    db = MagicMock()
    user_id = 1
    
    # Mock transactions (Domestic sale 40,000 BRL)
    tx1 = Transaction(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        tx_type="sell",
        asset="BTC",
        total_value=Decimal("40000.00"),
        from_wallet="Foxbit" # Domestic
    )
    
    # Mock database results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [tx1]
    db.execute.return_value = mock_result
    
    # Execute
    status = ThresholdService.get_monthly_status(db, user_id, "BR")
    
    # Verify
    assert status["current_domestic"] == 40000.0
    assert status["remaining"] == 0.0
    assert "atingido" in status["advice"]

def test_brazil_offshore_separation():
    # Setup
    db = MagicMock()
    user_id = 1
    
    # Domestic sale 10k, Offshore sale 20k
    tx_dom = Transaction(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        tx_type="sell",
        asset="BTC",
        total_value=Decimal("10000.00"),
        from_wallet="NovaDAX"
    )
    tx_off = Transaction(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        tx_type="sell",
        asset="BTC",
        total_value=Decimal("20000.00"),
        from_wallet="Binance" # Offshore
    )
    
    # Mock database results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [tx_dom, tx_off]
    db.execute.return_value = mock_result
    
    # Execute
    status = ThresholdService.get_monthly_status(db, user_id, "BR")
    
    # Verify
    assert status["current_domestic"] == 10000.0
    assert status["current_offshore"] == 20000.0
    assert status["remaining"] == 25000.0 # Limit 35k - 10k domestic
