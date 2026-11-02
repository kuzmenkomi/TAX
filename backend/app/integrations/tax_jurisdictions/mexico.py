"""
Mexico Tax Jurisdiction Implementation
ISR (Impuesto Sobre la Renta) + IVA (Impuesto al Valor Agregado)
"""
from typing import List, Dict
from decimal import Decimal
from datetime import datetime
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class MexicoTaxJurisdiction(BaseTaxJurisdiction):
    """
    Mexico tax jurisdiction
    - ISR: Progressive tax on income (1.92% - 35%)
    - IVA: 16% standard VAT
    - Crypto: Classified as "Ingreso Acumulable" (ordinary income)
    - Forms: Anexo 1 (Capital gains), RFC
    """
    
    # Jurisdiction metadata
    code = "MX"
    name = "Mexico"
    currency = "MXN"
    vat_rate = Decimal("0.16")  # 16% IVA
    tax_rate = Decimal("0.175")  # Average ISR rate
    holding_period_days = 365
    
    # ISR Progressive rates 2024 (per SAT)
    # Rates are cumulative brackets
    ISR_RATES = [
        {"min": 0, "max": 7326.46, "rate": Decimal("0.0192")},           # 1.92% (Tax: 140.47)
        {"min": 7326.46, "max": 60667.50, "rate": Decimal("0.0640")},    # 6.4%  (Tax: 3410.33)
        {"min": 60667.50, "max": 120271.80, "rate": Decimal("0.1088")},  # 10.88% (Tax: 6513.62)
        {"min": 120271.80, "max": 200368.50, "rate": Decimal("0.1600")}, # 16%   (Tax: 12845.52)
        {"min": 200368.50, "max": 394788.04, "rate": Decimal("0.1792")}, # 17.92% (Tax: 34902.87)
        {"min": 394788.04, "max": 604855.32, "rate": Decimal("0.2240")}, # 22.4%  (Tax: 47207.92)
        {"min": 604855.32, "max": 1000000, "rate": Decimal("0.2400")},   # 24% and above
        {"min": 1000000, "max": float("inf"), "rate": Decimal("0.2400")} # 24% - top rate
    ]
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate ISR on capital gains
        
        Mexico: Capital gains are included in ordinary income (Ganancia de Capital)
        They are not separately taxed but part of cumulative annual income
        
        Args:
            gains: List of capital gain transactions
            calculation_method: 'fifo', 'lifo', or 'average_cost'
        
        Returns:
            TaxCalculationResult with ISR calculation
        """
        total_gain = self.calculate_total_gain(gains)
        
        # Calculate ISR using progressive rates
        isr_tax = TaxCalculator.apply_progressive_rates(total_gain, self.ISR_RATES)
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="ordinary_income",  # Mexico treats all income same
            tax_rate=self._calculate_average_rate(total_gain),
            calculated_tax=isr_tax,
            notes=f"ISR calculated on {total_gain} MXN using {calculation_method} method"
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """
        Calculate ISR on ordinary income (staking, mining, airdrops)
        
        Args:
            income_amount: Total income amount in MXN
        
        Returns:
            TaxCalculationResult with ISR calculation
        """
        isr_tax = TaxCalculator.apply_progressive_rates(income_amount, self.ISR_RATES)
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="ordinary_income",
            tax_rate=self._calculate_average_rate(income_amount),
            calculated_tax=isr_tax,
            notes="ISR on staking/mining/airdrops income"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """
        Calculate IVA (VAT)
        
        IVA is typically applied to purchased goods/services, not trading
        
        Args:
            transaction_value: Value of transaction
            transaction_type: Type of transaction (buy, sell, service)
        
        Returns:
            TaxCalculationResult with IVA calculation
        """
        vat = Decimal("0")
        
        # Only apply IVA on certain transactions
        if transaction_type in ["purchase", "service", "goods"]:
            vat = transaction_value * self.vat_rate
        
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="vat_base",
            tax_rate=self.vat_rate,
            calculated_tax=vat,
            notes="16% IVA (may be creditable if registered)"
        )
    
    def calculate_fee_deduction(
        self,
        fee_amount: Decimal
    ) -> Decimal:
        """
        Calculate deductible fees
        
        Trading fees are deductible from capital gains
        
        Args:
            fee_amount: Fee amount in MXN
        
        Returns:
            Deductible amount
        """
        # In Mexico, reasonable trading fees are fully deductible
        return fee_amount
    
    def apply_progressive_rates(
        self,
        taxable_amount: Decimal
    ) -> Decimal:
        """
        Apply progressive ISR rates
        
        Args:
            taxable_amount: Taxable income amount
        
        Returns:
            Calculated ISR tax
        """
        return TaxCalculator.apply_progressive_rates(taxable_amount, self.ISR_RATES)
    
    def _calculate_average_rate(self, amount: Decimal) -> Decimal:
        """
        Calculate average tax rate for given amount
        
        Args:
            amount: Amount to calculate effective rate for
        
        Returns:
            Effective tax rate
        """
        if amount == 0:
            return Decimal("0")
        
        tax = TaxCalculator.apply_progressive_rates(amount, self.ISR_RATES)
        rate = (tax / amount * 100).quantize(Decimal("0.01"))
        return rate
    
    def get_form_requirements(self) -> Dict:
        """
        Get required tax forms for filing
        
        Returns:
            Dictionary of required forms
        """
        return {
            "primary_form": "DECLARACIÓN ANUAL",
            "schedules": [
                "Anexo 1 - Ingresos Acumulables",
                "Anexo 2 - Operaciones con Terceros",
                "Anexo 5 - Deducible Expenses"
            ],
            "required_docs": [
                "RFC (Registro Federal de Contribuyentes)",
                "Proof of residence",
                "Bank statements"
            ]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """
        Get tax filing deadline
        
        Mexico: April 30th of following year
        
        Args:
            year: Tax year
        
        Returns:
            Filing deadline as string
        """
        return f"April 30, {year + 1}"
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "filing_frequency": "yearly",
            "filing_authority": "SAT (Servicio de Administración Tributaria)",
            "forms_required": self.get_form_requirements(),
            "holding_period_days": self.holding_period_days
        }
