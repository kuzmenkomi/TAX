import pytest
from datetime import datetime, timezone
from collections import deque
from app.accounting.calculator import Lot, _consume_fifo, _consume_lifo, _consume_hifo

def test_fifo_logic():
    lots = deque([
        Lot(quantity=1.0, unit_cost=1000.0, timestamp=100),
        Lot(quantity=2.0, unit_cost=2000.0, timestamp=200),
    ])
    
    # Sell 1.5 units
    cost_basis, consumed = _consume_fifo(lots, 1.5)
    
    # FIFO: 1.0 from first lot ($1000) + 0.5 from second lot ($1000) = $2000
    assert cost_basis == 2000.0
    assert len(consumed) == 2
    assert consumed[0]["amount"] == 1.0
    assert consumed[1]["amount"] == 0.5
    assert len(lots) == 1
    assert lots[0].quantity == 1.5

def test_lifo_logic():
    lots = deque([
        Lot(quantity=1.0, unit_cost=1000.0, timestamp=100),
        Lot(quantity=2.0, unit_cost=2000.0, timestamp=200),
    ])
    
    # Sell 1.5 units
    cost_basis, consumed = _consume_lifo(lots, 1.5)
    
    # LIFO: 1.5 from second lot (last bought) = 1.5 * $2000 = $3000
    assert cost_basis == 3000.0
    assert len(consumed) == 1
    assert consumed[0]["amount"] == 1.5
    assert len(lots) == 2
    assert lots[0].quantity == 1.0
    assert lots[1].quantity == 0.5

def test_hifo_logic():
    lots = deque([
        Lot(quantity=1.0, unit_cost=3000.0, timestamp=100), # Most expensive
        Lot(quantity=2.0, unit_cost=1000.0, timestamp=200),
        Lot(quantity=0.5, unit_cost=5000.0, timestamp=300), # Most expensive now
    ])
    
    # Sell 1.0 unit
    cost_basis, consumed = _consume_hifo(lots, 1.0)
    
    # HIFO: 0.5 from $5000 lot ($2500) + 0.5 from $3000 lot ($1500) = $4000
    assert cost_basis == 4000.0
    assert len(consumed) == 2
    assert consumed[0]["amount"] == 0.5
    assert consumed[1]["amount"] == 0.5
    
    # Remaining
    assert len(lots) == 2
    # The $5000 lot is gone, $3000 lot has 0.5 left, $1000 lot has 2.0 left

def test_insufficient_funds():
    lots = deque([Lot(quantity=1.0, unit_cost=1000.0, timestamp=100)])
    with pytest.raises(ValueError, match="Недостаточно монет"):
        _consume_fifo(lots, 2.0)

def test_partial_matching_precision():
    # Test floating point precision handling (1e-12 threshold)
    lots = deque([Lot(quantity=1.0000000000001, unit_cost=1000.0, timestamp=100)])
    cost_basis, consumed = _consume_fifo(lots, 1.0)
    assert cost_basis == 1000.0
    assert len(lots) == 0 # Should be popped because < 1e-12 remaining
