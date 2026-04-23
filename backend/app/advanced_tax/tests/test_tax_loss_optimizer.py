"""
Tax-Loss Harvesting Tests - Unit & Integration Tests
Tests for FIFO/LIFO/AVCO, wash-sale rules, liquidity, and fee calculations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta


class TestWashSaleRules:
    """Test country-specific wash-sale rules"""
    
    def test_us_wash_sale_30_days(self):
        """USA: 30-day wash-sale rule"""
        from app.advanced_tax.services.wash_sale_rules import WashSaleRules
        
        sell_date = datetime.now() - timedelta(days=10)
        is_violation, days_remaining, msg = WashSaleRules.check_wash_sale_violation("US", sell_date)
        
        assert is_violation == True
        assert days_remaining == 20
        assert "20" in msg
    
    def test_us_after_30_days_clear(self):
        """USA: After 30 days, no violation"""
        from app.advanced_tax.services.wash_sale_rules import WashSaleRules
        
        sell_date = datetime.now() - timedelta(days=40)
        is_violation, days_remaining, msg = WashSaleRules.check_wash_sale_violation("US", sell_date)
        
        assert is_violation == False
        assert days_remaining == 0
    
    def test_mexico_no_wash_sale(self):
        """Mexico: No wash-sale rule"""
        from app.advanced_tax.services.wash_sale_rules import WashSaleRules
        
        sell_date = datetime.now() - timedelta(days=5)
        is_violation, days_remaining, msg = WashSaleRules.check_wash_sale_violation("MX", sell_date)
        
        assert is_violation == False
        assert days_remaining == 0
        assert "no wash-sale" in msg.lower()
    
    def test_get_rebuy_date_us(self):
        """Get earliest rebuy date for USA"""
        from app.advanced_tax.services.wash_sale_rules import WashSaleRules
        
        sell_date = datetime(2024, 1, 1)
        rebuy_date = WashSaleRules.get_rebuy_date("US", sell_date)
        
        # Should be 31 days later (30 day rule + 1)
        expected = datetime(2024, 2, 1)
        assert rebuy_date.date() == expected.date()


class TestCostBasisCalculator:
    """Test cost basis methods (FIFO, LIFO, AVCO)"""
    
    @pytest.fixture
    def sample_lots(self):
        """Create sample purchase lots"""
        from app.advanced_tax.services.cost_basis_calculator import CostBasisLot
        
        return [
            CostBasisLot("BTC", Decimal("0.5"), Decimal("40000"), datetime.now() - timedelta(days=365)),
            CostBasisLot("BTC", Decimal("0.5"), Decimal("45000"), datetime.now() - timedelta(days=180)),
            CostBasisLot("BTC", Decimal("0.5"), Decimal("35000"), datetime.now() - timedelta(days=30)),
        ]
    
    def test_fifo_oldest_first(self, sample_lots):
        """FIFO: Sell oldest lots first - should get high cost basis"""
        from app.advanced_tax.services.cost_basis_calculator import CostBasisCalculator
        
        qty_to_sell = Decimal("1.0")
        avg_cost, sold_lots = CostBasisCalculator.fifo(sample_lots, qty_to_sell)
        
        # FIFO should sell oldest (40000) + oldest (45000) + partial newest
        expected_avg = (Decimal("40000") + Decimal("45000")) / 2
        assert abs(avg_cost - expected_avg) < Decimal("1000")
    
    def test_lifo_newest_first(self, sample_lots):
        """LIFO: Sell newest lots first - should get low cost basis (maximize loss)"""
        from app.advanced_tax.services.cost_basis_calculator import CostBasisCalculator
        
        qty_to_sell = Decimal("1.0")
        avg_cost, sold_lots = CostBasisCalculator.lifo(sample_lots, qty_to_sell)
        
        # LIFO should sell newest (35000) + middle (45000) + partial oldest
        expected_avg = (Decimal("35000") + Decimal("45000")) / 2
        assert abs(avg_cost - expected_avg) < Decimal("1000")
    
    def test_avco_weighted_average(self, sample_lots):
        """AVCO: Weighted average cost should be middle value"""
        from app.advanced_tax.services.cost_basis_calculator import CostBasisCalculator
        
        qty_to_sell = Decimal("1.0")
        avg_cost, sold_lots = CostBasisCalculator.avco(sample_lots, qty_to_sell)
        
        # AVCO = (0.5*40000 + 0.5*45000 + 0.5*35000) / 1.5
        expected_avg = (Decimal("40000") + Decimal("45000") + Decimal("35000")) / 3
        assert abs(avg_cost - expected_avg) < Decimal("100")
    
    def test_optimal_loss_uses_lifo(self, sample_lots):
        """find_optimal_loss should choose LIFO for maximum loss"""
        from app.advanced_tax.services.cost_basis_calculator import CostBasisCalculator
        
        qty_to_sell = Decimal("1.0")
        current_price = Decimal("30000")  # Price is down
        
        best_method, loss, cost = CostBasisCalculator.find_optimal_loss(
            sample_lots, qty_to_sell, current_price
        )
        
        assert best_method == "LIFO"  # Should choose LIFO for max loss
        assert loss > 0


class TestLiquidityChecker:
    """Test liquidity assessment"""
    
    def test_btc_ultra_liquid(self):
        """BTC should be ultra-liquid"""
        from app.advanced_tax.services.liquidity_checker import LiquidityChecker
        
        score, desc, slippage = LiquidityChecker.assess_liquidity(
            "BTC",
            market_cap=Decimal("1000000000000"),  # $1T
            volume_24h=Decimal("30000000000")  # $30B
        )
        
        assert score == 100
        assert slippage < Decimal("0.1")
    
    def test_illiquid_small_cap(self):
        """Small cap under $10M should be low liquidity"""
        from app.advanced_tax.services.liquidity_checker import LiquidityChecker
        
        score, desc, slippage = LiquidityChecker.assess_liquidity(
            "XYZ",
            market_cap=Decimal("5000000"),  # $5M
            volume_24h=Decimal("100000")  # $100k
        )
        
        assert score < 50
    
    def test_can_sell_major_asset(self):
        """Should be able to sell BTC without slippage issues"""
        from app.advanced_tax.services.liquidity_checker import LiquidityChecker
        
        can_sell, reason = LiquidityChecker.can_sell_without_slippage(
            "BTC",
            Decimal("0.1"),  # 0.1 BTC
            volume_24h=Decimal("30000000000")
        )
        
        assert can_sell == True
    
    def test_cannot_sell_huge_amount(self):
        """Cannot sell amount that exceeds volume"""
        from app.advanced_tax.services.liquidity_checker import LiquidityChecker
        
        can_sell, reason = LiquidityChecker.can_sell_without_slippage(
            "BTC",
            Decimal("1000000"),  # 1M BTC (insane)
            volume_24h=Decimal("30000000000")
        )
        
        assert can_sell == False


class TestTaxLossOptimizer:
    """Integration tests for TaxLossOptimizer"""
    
    def test_priority_scoring(self):
        """Test priority score calculation"""
        from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
        from decimal import Decimal
        
        # Create mock optimizer
        optimizer = TaxLossOptimizer(None, 1, "US")
        
        # High tax benefit + high liquidity + moderate volatility = high score
        score = optimizer._calculate_priority_score(
            tax_benefit=Decimal("1000"),
            liquidity_score=90,
            volatility=10,
            loss_amount=Decimal("5000")
        )
        
        assert score > 70
    
    def test_risk_assessment_low_vol(self):
        """Low volatility = low risk"""
        from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
        
        optimizer = TaxLossOptimizer(None, 1, "US")
        risk = optimizer._assess_risk_level(3)
        
        assert risk == "low"
    
    def test_risk_assessment_high_vol(self):
        """High volatility = high risk"""
        from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
        
        optimizer = TaxLossOptimizer(None, 1, "US")
        risk = optimizer._assess_risk_level(30)
        
        assert risk == "high"
    
    def test_tax_rate_by_country(self):
        """Different countries have different tax rates"""
        from app.advanced_tax.services.tax_loss_optimizer import TaxLossOptimizer
        
        opt_us = TaxLossOptimizer(None, 1, "US")
        opt_br = TaxLossOptimizer(None, 1, "BR")
        opt_mx = TaxLossOptimizer(None, 1, "MX")
        
        rate_us = opt_us._get_marginal_tax_rate()
        rate_br = opt_br._get_marginal_tax_rate()
        rate_mx = opt_mx._get_marginal_tax_rate()
        
        assert rate_us == 24.0
        assert rate_br == 15.0
        assert rate_mx == 35.0


# Run tests with: pytest advanced_tax_engine/tests/test_tax_loss_optimizer.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
