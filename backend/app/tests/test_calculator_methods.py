import pytest
from collections import deque
from app.accounting.calculator import _consume_lifo, _consume_hifo, Lot, calculate_pnl, TaxRules
import pandas as pd
from datetime import datetime, timezone

class TestLifoConsume:
    def test_lifo_order(self):
        """Last-In, First-Out: sell newest lots first."""
        lots = deque([
            Lot(quantity=1.0, unit_cost=100.0, timestamp=100),
            Lot(quantity=1.0, unit_cost=200.0, timestamp=200),
        ])
        cost, consumed = _consume_lifo(lots, 1.5)
        # 1.0 * 200 (newest) + 0.5 * 100 (older) = 250
        assert cost == pytest.approx(250.0)
        assert len(lots) == 1
        assert lots[0].quantity == pytest.approx(0.5)
        assert lots[0].unit_cost == 100.0

class TestHifoConsume:
    def test_hifo_order(self):
        """Highest-In, First-Out: sell most expensive lots first."""
        lots = deque([
            Lot(quantity=1.0, unit_cost=100.0, timestamp=100),
            Lot(quantity=1.0, unit_cost=300.0, timestamp=200),
            Lot(quantity=1.0, unit_cost=200.0, timestamp=300),
        ])
        cost, consumed = _consume_hifo(lots, 1.5)
        # 1.0 * 300 (most expensive) + 0.5 * 200 (next expensive) = 400
        assert cost == pytest.approx(400.0)
        assert len(lots) == 2
        # Check remaining quantities
        remaining_quantities = [l.quantity for l in lots]
        assert 1.0 in remaining_quantities # The $100 lot
        assert 0.5 in remaining_quantities # The $200 lot

class FakePriceService:
    def get_historical_price_usd(self, asset, timestamp):
        return 1000.0

def test_calculate_pnl_methods():
    df = pd.DataFrame([
        {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 10000, "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        {"type": "BUY", "asset": "BTC", "amount": 1.0, "price": 20000, "timestamp": datetime(2024, 1, 2, tzinfo=timezone.utc)},
        {"type": "SELL", "asset": "BTC", "amount": 1.0, "price": 25000, "timestamp": datetime(2024, 1, 3, tzinfo=timezone.utc)},
    ])
    
    ps = FakePriceService()
    
    # FIFO: cost = 10000, profit = 15000
    res_fifo = calculate_pnl(df, [], ps, rules=TaxRules(cost_basis_method="FIFO"))
    assert res_fifo["total_realized_pnl_usd"] == 15000.0
    
    # LIFO: cost = 20000, profit = 5000
    # We need a fresh inventory for each run, but calculate_pnl handles it inside
    res_lifo = calculate_pnl(df, [], ps, rules=TaxRules(cost_basis_method="LIFO"))
    assert res_lifo["total_realized_pnl_usd"] == 5000.0
    
    # HIFO: cost = 20000, profit = 5000
    res_hifo = calculate_pnl(df, [], ps, rules=TaxRules(cost_basis_method="HIFO"))
    assert res_hifo["total_realized_pnl_usd"] == 5000.0
