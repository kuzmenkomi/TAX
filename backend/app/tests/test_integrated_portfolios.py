import pytest
from decimal import Decimal
from typing import Dict, Any

from app.countries.base.tax_calculator import BaseTaxCalculator
from app.countries.br.config import Brazil
from app.countries.mx.config import Mexico
from app.countries.ar.config import Argentina
from app.countries.co.config import Colombia
from app.countries.pe.config import Peru
from app.countries.cl.config import Chile
from app.countries.gt.config import Guatemala
from app.countries.ec.config import Ecuador
from app.countries.uy.config import Uruguay
from app.countries.cr.config import CostaRica
from app.countries.hn.config import Honduras
from app.countries.bo.config import Bolivia

COUNTRIES = [
    Brazil, Mexico, Argentina, Colombia, Peru, Chile,
    Guatemala, Ecuador, Uruguay, CostaRica, Honduras, Bolivia
]

@pytest.fixture(params=COUNTRIES)
def calculator(request):
    return BaseTaxCalculator(request.param())

class TestIntegratedPortfolios:
    """
    Final Audit: Integrated testing of the entire tax engine with mixed input data.
    Ensures that components (Income, CG, Crypto, etc.) work together without drift.
    """

    def test_scenario_simple_salary(self, calculator):
        """Testing pure progressive income tax for all countries."""
        amount = 10000000.0
        if calculator.country.currency in ["USD", "PAB"]: amount = 50000.0
        
        result = calculator.calculate_total_tax_liability(gross_income=amount)
        
        assert result["total_tax_liability"] >= 0
        assert "income_tax" in result["components"]
        # Basic check: income_tax should be the main driver
        assert result["total_tax_liability"] >= result["components"]["income_tax"]["income_tax"]

    def test_scenario_mixed_investor(self, calculator):
        """Testing Salary + Capital Gains + Crypto."""
        salary = 5000000.0
        capital_gains = 1000000.0
        crypto_gains = 2000000.0
        
        if calculator.country.currency in ["USD"]:
            salary, capital_gains, crypto_gains = 30000.0, 5000.0, 10000.0

        result = calculator.calculate_total_tax_liability(
            gross_income=salary,
            capital_gains=capital_gains,
            crypto_activity={"crypto_gains": crypto_gains}
        )
        
        # Verify all components are present in breakdown
        components = result["components"]
        assert "income_tax" in components
        assert "capital_gains_tax" in components
        assert "cryptocurrency_tax" in components
        
        # Verify summation
        expected_total = (
            float(components["income_tax"]["income_tax"]) + 
            float(components["capital_gains_tax"]["capital_gains_tax"]) + 
            float(components["cryptocurrency_tax"]["total_cryptocurrency_tax"]) +
            float(components["vat_tax"])
        )
        assert result["total_tax_liability"] == pytest.approx(expected_total, rel=1e-5)

    def test_scenario_high_deductions(self, calculator):
        """Testing that deductions correctly reduce taxable income."""
        income = 10000000.0
        if calculator.country.currency == "USD": income = 50000.0
        
        deductions = {
            "health": 1000000.0,
            "education": 1000000.0
        }
        
        result_none = calculator.calculate_total_tax_liability(gross_income=income)
        result_deduct = calculator.calculate_total_tax_liability(gross_income=income, deductions=deductions)
        
        assert result_deduct["components"]["income_tax"]["taxable_income"] < income
        assert result_deduct["total_tax_liability"] <= result_none["total_tax_liability"]
        assert result_deduct["total_tax_liability"] >= 0

    def test_scenario_extreme_whale(self, calculator):
        """Testing massive inputs."""
        huge_income = 1000000000.0 
        if calculator.country.currency == "USD": huge_income = 5000000.0
        
        result = calculator.calculate_total_tax_liability(gross_income=huge_income)
        
        assert result["effective_tax_rate"] >= 0
        assert result["total_tax_liability"] > 0
        
    def test_scenario_loss_clamping(self, calculator):
        """Testing that losses don't result in negative tax."""
        result = calculator.calculate_total_tax_liability(
            gross_income=10000.0,
            capital_gains=-5000.0
        )
        
        assert result["components"]["capital_gains_tax"]["capital_gains_tax"] == 0
        assert result["total_tax_liability"] >= 0

    @pytest.mark.parametrize("input_val", [0.0, 0.01, 999999.99])
    def test_type_precision_fuzz(self, calculator, input_val):
        """Final check for type consistency across 12 countries."""
        result = calculator.calculate_total_tax_liability(gross_income=input_val, capital_gains=input_val)
        assert isinstance(result["total_tax_liability"], (float, Decimal, int))
