# Guatemala Tax Calculator
# Inherits from BaseTaxCalculator and implements Guatemala-specific logic

from typing import Dict, Any, List
from app.countries.base import BaseTaxCalculator
from app.countries.gt.config import Guatemala


class TaxCalculator(BaseTaxCalculator):
    """
    Guatemala-specific tax calculator.
    
    Implements:
    - ISR (Income Tax) calculation with Guatemala brackets
    - DeFi/Crypto tax treatment
    - Local deduction rules
    """

    def __init__(self):
        """Initialize with Guatemala definition"""
        super().__init__(Guatemala())

    def calculate_isr(
        self,
        gross_income: float,
        deductions: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate ISR (Impuesto Sobre la Renta).
        
        Guatemala's main income tax with special rules:
        - Non-residents taxed at flat 31% on Guatemalan-source income
        - Residents on worldwide income
        - Certain agricultural income may have exemptions
        
        Args:
            gross_income: Total income
            deductions: Applicable deductions
            
        Returns:
            ISR calculation breakdown
        """
        deductions = deductions or {}
        
        # Get allowed deductions for Guatemala
        allowed_deductions = self.country.get_applicable_deductions(gross_income)
        allowed_deductions.update(deductions)
        
        # Calculate using parent method
        income_tax_calc = self.calculate_income_tax(
            gross_income,
            allowed_deductions,
        )
        
        # Add Guatemala-specific fields
        income_tax_calc["tax_form"] = "F-101"
        income_tax_calc["filing_deadline"] = self.country.filing_deadline_full
        income_tax_calc["currency"] = self.country.currency
        
        return income_tax_calc

    def calculate_business_income_tax(
        self,
        gross_revenue: float,
        business_expenses: float,
        crypto_trading_gains: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tax on business income in Guatemala.
        
        Self-employed/business owners must file:
        - Net income = gross - expenses
        - Subject to ISR rates
        - VAT applies on transactions
        
        Args:
            gross_revenue: Total business revenue
            business_expenses: Documented business expenses
            crypto_trading_gains: Any crypto trading gains
            
        Returns:
            Business income tax breakdown
        """
        # Net business income
        net_income = max(0, gross_revenue - business_expenses)
        
        # Add crypto gains
        taxable_income = net_income + crypto_trading_gains
        
        # Calculate ISR on combined income
        isr_calc = self.calculate_isr(taxable_income)
        
        # Calculate VAT (12% on services, 12% on goods)
        vat_calculated = gross_revenue * 0.12
        
        return {
            "business_income": {
                "gross_revenue": gross_revenue,
                "business_expenses": business_expenses,
                "net_income": net_income,
            },
            "crypto_gains": crypto_trading_gains,
            "isr_calculation": isr_calc,
            "vat_liability": {
                "gross_revenue": gross_revenue,
                "vat_rate": 0.12,
                "vat_amount": vat_calculated,
            },
            "total_tax": isr_calc["income_tax"] + vat_calculated,
            "currency": self.country.currency,
        }

    def calculate_crypto_tax_guatemala(
        self,
        transactions: List[Dict[str, Any]],
        staking_rewards: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tax on cryptocurrency activities in Guatemala.
        
        Guatemala treats crypto like capital assets:
        - Gains subject to 31% capital gains tax
        - Staking/yield treated as ordinary income
        - Mining treated as business income if recurring
        
        Args:
            transactions: List of crypto transactions with costs and proceeds
            staking_rewards: Income from staking activities
            
        Returns:
            Crypto tax breakdown
        """
        total_gains = sum(t.get("gain", 0) for t in transactions)
        
        # Capital gains on crypto trading (31%)
        gains_tax = self.calculate_capital_gains_tax(total_gains)
        
        # Staking income treated as ordinary income
        staking_tax = self.calculate_income_tax(staking_rewards)
        
        return {
            "transaction_count": len(transactions),
            "total_gains": total_gains,
            "staking_rewards": staking_rewards,
            "capital_gains_tax": gains_tax,
            "staking_income_tax": staking_tax,
            "total_crypto_tax": gains_tax["income_tax"] + staking_tax["income_tax"],
            "note": "Staking treated as ordinary income, gains as capital gains",
            "currency": self.country.currency,
        }

    def check_filing_obligation(
        self,
        gross_income: float,
        self_employed: bool = False,
    ) -> Dict[str, bool]:
        """
        Determine if taxpayer must file in Guatemala.
        
        Filing is mandatory if:
        - Any income reported to social security
        - Self-employed earning above threshold
        - Has deductible expenses
        - Non-resident with Guatemalan-source income
        
        Args:
            gross_income: Total income
            self_employed: Is taxpayer self-employed?
            
        Returns:
            Filing requirements
        """
        filing_required = {
            "must_file_isr": False,
            "must_file_f104": False,
            "must_register_vat": False,
        }
        
        # ISR filing threshold
        if gross_income > 0:
            filing_required["must_file_isr"] = True
        
        # F-104 required if income > 43,600
        if gross_income > 43_600:
            filing_required["must_file_f104"] = True
        
        # VAT registration if self-employed with significant revenue
        if self_employed and gross_income > 100_000:
            filing_required["must_register_vat"] = True
        
        return filing_required

    def estimate_tax_liability(
        self,
        gross_income: float,
        capital_gains: float = 0,
        crypto_activity: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Estimate total tax liability for Guatemala.
        
        Quick calculation for tax planning purposes.
        """
        crypto_activity = crypto_activity or {}
        
        # Income tax
        isr = self.calculate_isr(gross_income)
        
        # Capital gains (31% flat)
        cap_gains_tax = self.calculate_capital_gains_tax(capital_gains)
        
        # Crypto (simplified)
        crypto_gains = crypto_activity.get("trading_gains", 0)
        crypto_tax = self.calculate_capital_gains_tax(crypto_gains)
        
        total_tax = isr["income_tax"] + cap_gains_tax["capital_gains_tax"] + crypto_tax["capital_gains_tax"]
        total_income = gross_income + capital_gains + crypto_gains
        effective_rate = total_tax / total_income if total_income > 0 else 0
        
        return {
            "income_tax": isr["income_tax"],
            "capital_gains_tax": cap_gains_tax["capital_gains_tax"],
            "crypto_tax": crypto_tax["capital_gains_tax"],
            "total_estimated_tax": total_tax,
            "total_income": total_income,
            "effective_tax_rate": effective_rate,
            "currency": self.country.currency,
            "timezone": "CST (UTC-6)",
            "filing_deadline": self.country.filing_deadline_full,
        }
