# Comprehensive tests for Guatemala implementation

import pytest
from app.countries.gt.config import Guatemala
from app.countries.gt.calculator import TaxCalculator
from app.countries.gt.api import SATClient
from app.countries.base import TaxType, SubmissionStatus


class TestGuatemalaConfiguration:
    """Test Guatemala configuration"""

    @pytest.fixture
    def config(self):
        return Guatemala()

    def test_country_identifiers(self, config):
        """Test basic country identifiers"""
        assert config.country_code == "GT"
        assert config.country_name == "Guatemala"
        assert config.currency == "GTQ"
        assert config.currency_symbol == "Q"

    def test_tax_authority(self, config):
        """Test tax authority information"""
        assert config.tax_authority == "SAT"
        assert config.has_api is True
        assert "sat.gob.gt" in config.api_base_url.lower()

    def test_tax_rates(self, config):
        """Test Guatemala tax rates"""
        rates = config.get_tax_rates()
        
        # Test income tax brackets
        assert TaxType.INCOME_TAX in rates
        income_tax_brackets = rates[TaxType.INCOME_TAX]
        assert len(income_tax_brackets) == 3
        
        # Verify bracket values
        assert income_tax_brackets[0].min_amount == 0
        assert income_tax_brackets[0].max_amount == 5_000
        assert income_tax_brackets[0].rate == 0.05
        
        assert income_tax_brackets[1].rate == 0.07
        assert income_tax_brackets[2].rate == 0.31
        
        # Test capital gains
        assert TaxType.CAPITAL_GAINS in rates
        assert rates[TaxType.CAPITAL_GAINS][0].rate == 0.31
        
        # Test VAT
        assert TaxType.VAT in rates
        assert rates[TaxType.VAT][0].rate == 0.12

    def test_deductions(self, config):
        """Test Guatemala deductions"""
        deductions = config.get_deductions()
        
        # Test common deductions exist
        assert "health_insurance" in deductions
        assert "housing" in deductions
        assert "education" in deductions

    def test_tax_forms(self, config):
        """Test Guatemala tax forms"""
        forms = config.get_tax_forms()
        
        # F-101 is primary form
        assert "F-101" in forms
        assert forms["F-101"].required is True
        assert forms["F-101"].deadline == "2024-04-30"
        
        # F-104 is conditional
        assert "F-104" in forms
        assert forms["F-104"].required is False

    def test_nit_validation(self, config):
        """Test NIT validation"""
        # Valid NIT format (should pass basic check)
        assert config.validate_taxpayer_id("12345678901") is True
        
        # Invalid formats
        assert config.validate_taxpayer_id("123") is False  # Too short
        assert config.validate_taxpayer_id("ABCDEFGHIJK") is False  # Letters
        assert config.validate_taxpayer_id("") is False  # Empty

    def test_currency_formatting(self, config):
        """Test currency formatting"""
        # With symbol
        formatted = config.format_currency(50000)
        assert "Q" in formatted
        assert "50,000" in formatted
        
        # Without symbol
        formatted = config.format_currency(50000, symbol=False)
        assert "GTQ" in formatted
        assert "50,000" in formatted

    def test_country_info(self, config):
        """Test comprehensive country info"""
        info = config.get_country_info()
        assert info["code"] == "GT"
        assert info["name"] == "Guatemala"
        assert "tax_authority" in info


class TestGuatemalaTaxCalculator:
    """Test Guatemala tax calculator"""

    @pytest.fixture
    def calculator(self):
        return TaxCalculator()

    def test_calculator_initialization(self, calculator):
        """Test calculator initializes with Guatemala"""
        assert calculator.country.country_code == "GT"
        assert calculator.country.country_name == "Guatemala"

    def test_isr_calculation_simple(self, calculator):
        """Test simple ISR calculation"""
        result = calculator.calculate_isr(gross_income=10_000)
        
        assert result["gross_income"] == 10_000
        assert result["income_tax"] > 0
        assert "tax_form" in result
        assert result["tax_form"] == "F-101"

    def test_isr_calculation_brackets(self, calculator):
        """Test ISR calculation with multiple brackets"""
        # Income in bottom bracket (0-5000 @ 5%)
        result1 = calculator.calculate_isr(4_000)
        expected_tax1 = 4_000 * 0.05
        assert abs(result1["income_tax"] - expected_tax1) < 1
        
        # Income spanning brackets
        result2 = calculator.calculate_isr(10_000)
        # 5000 * 0.05 + 5000 * 0.07
        expected_tax2 = (5_000 * 0.05) + (5_000 * 0.07)
        assert abs(result2["income_tax"] - expected_tax2) < 1

    def test_isr_with_deductions(self, calculator):
        """Test ISR calculation with deductions"""
        deductions = {
            "health_insurance": 1_000,
            "education": 500,
        }
        
        result = calculator.calculate_isr(
            gross_income=30_000,
            deductions=deductions,
        )
        
        assert result["total_deductions"] >= 1_500
        assert result["taxable_income"] <= 28_500
        assert result["income_tax"] < calculator.calculate_isr(30_000)["income_tax"]

    def test_capital_gains_tax(self, calculator):
        """Test capital gains tax calculation"""
        result = calculator.calculate_capital_gains_tax(capital_gains=10_000)
        
        # Guatemala capital gains: 31% flat
        expected = 10_000 * 0.31
        assert abs(result["capital_gains_tax"] - expected) < 1
        assert result["effective_rate"] == 0.31

    def test_crypto_tax_calculation(self, calculator):
        """Test cryptocurrency tax calculation"""
        transactions = [
            {"gain": 1_000},
            {"gain": 2_000},
            {"gain": 500},
        ]
        
        result = calculator.calculate_crypto_tax_guatemala(
            transactions=transactions,
            staking_rewards=1_000,
        )
        
        assert result["total_gains"] == 3_500
        assert result["staking_rewards"] == 1_000
        assert "capital_gains_tax" in result
        assert "staking_income_tax" in result
        assert result["total_crypto_tax"] > 0

    def test_filing_obligation_check(self, calculator):
        """Test filing obligation determination"""
        # No income
        result = calculator.check_filing_obligation(0)
        assert result["must_file_isr"] is False
        
        # With income
        result = calculator.check_filing_obligation(30_000)
        assert result["must_file_isr"] is True
        assert result["must_file_f104"] is False  # Below 43,600 threshold
        
        # High income
        result = calculator.check_filing_obligation(100_000)
        assert result["must_file_isr"] is True
        assert result["must_file_f104"] is True
        assert result["must_register_vat"] is False  # Not self-employed
        
        # Self-employed high income
        result = calculator.check_filing_obligation(200_000, self_employed=True)
        assert result["must_register_vat"] is True

    def test_tax_estimate(self, calculator):
        """Test tax estimation"""
        estimate = calculator.estimate_tax_liability(
            gross_income=50_000,
            capital_gains=5_000,
            crypto_activity={"trading_gains": 2_000},
        )
        
        assert estimate["income_tax"] > 0
        assert estimate["capital_gains_tax"] > 0
        assert estimate["crypto_tax"] > 0
        assert estimate["total_estimated_tax"] > 0
        assert 0 < estimate["effective_tax_rate"] < 1


class TestSATClient:
    """Test SAT Guatemala API client"""

    @pytest.fixture
    def client(self):
        return SATClient(nit="12345678901", password="test_password")

    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.nit == "12345678901"
        assert client.jurisdiction_code == "GT"

    def test_nit_validation(self, client):
        """Test NIT validation in client"""
        # Valid NIT
        client.nit = "12345678901"
        assert client._validate_nit() is True
        
        # Invalid NIT
        client.nit = "123"
        assert client._validate_nit() is False

    def test_compliance_check(self, client):
        """Test compliance check"""
        filing_data = {
            "nit": "12345678901",
            "name": "John Doe",
            "income": 50_000,
            "deductions": {"health": 1_000},
            "tax_paid": 5_000,
        }
        
        result = client.check_compliance(filing_data)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_compliance_check_missing_fields(self, client):
        """Test compliance check with missing fields"""
        filing_data = {
            "name": "John Doe",
            # Missing required fields
        }
        
        result = client.check_compliance(filing_data)
        assert result.is_valid is False
        assert len(result.issues) > 0

    def test_compliance_check_excessive_deductions(self, client):
        """Test deduction limit validation"""
        filing_data = {
            "nit": "12345678901",
            "name": "John Doe",
            "income": 10_000,
            "deductions": {"health": 9_000},  # 90% of income!
            "tax_paid": 0,
        }
        
        result = client.check_compliance(filing_data)
        assert len(result.warnings) > 0  # Should warn about high deductions

    def test_get_filing_forms(self, client):
        """Test form listing"""
        forms = client.get_filing_forms(2024)
        
        assert "F-101" in forms
        assert "F-104" in forms
        assert forms["F-101"]["required"] is True
        assert forms["F-104"]["required"] is False


class TestGuatemalaIntegration:
    """Integration tests for Guatemala system"""

    def test_full_tax_workflow(self):
        """Test complete tax filing workflow"""
        # 1. Get Guatemala config
        config = Guatemala()
        assert config.country_code == "GT"
        
        # 2. Use calculator
        calc = TaxCalculator()
        result = calc.calculate_isr(gross_income=50_000)
        assert result["income_tax"] > 0
        
        # 3. Validate with SAT client
        client = SATClient("12345678901")
        filing_data = {
            "nit": "12345678901",
            "name": "Test Taxpayer",
            "income": result["gross_income"],
            "deductions": result["deduction_breakdown"],
            "tax_paid": result["income_tax"],
        }
        
        compliance = client.check_compliance(filing_data)
        assert compliance.is_valid is True

    def test_progressive_tax_calculation(self):
        """Test progressive taxation across brackets"""
        calc = TaxCalculator()
        
        # Test amounts at bracket boundaries
        test_cases = [
            (5_000, 250),      # Exactly at bracket 1 limit
            (10_000, 600),     # Across brackets 1 and 2
            (25_000, 2_100),   # Across all brackets
        ]
        
        for income, expected_tax in test_cases:
            result = calc.calculate_isr(income)
            assert abs(result["income_tax"] - expected_tax) < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
