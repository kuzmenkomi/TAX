"""
Argentina Tax Jurisdiction Implementation
Ganancias (Capital Gains Tax) + IVA (Value Added Tax)
"""
from typing import List, Dict
from decimal import Decimal
from datetime import datetime
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class ArgentinaTaxJurisdiction(BaseTaxJurisdiction):
    """
    Argentina tax jurisdiction
    - Ganancias: Progressive tax on capital gains (5% - 45%)
    - IVA: 21% standard VAT
    - CER Adjustment: Inflation adjustment using CER (Coeficiente de Estabilización)
    - Crypto: Classified as "Renta Financiera" (financial income)
    - Forms: F. 573 (Assets), F. 1020 (Gain Calculation)
    """
    
    # Jurisdiction metadata
    code = "AR"
    name = "Argentina"
    currency = "ARS"
    vat_rate = Decimal("0.21")  # 21% IVA
    tax_rate = Decimal("0.15")  # Average Ganancias rate
    holding_period_days = 365
    
    # Ganancias Progressive rates (2024)
    GANANCIAS_RATES = [
        {"min": 0, "max": 118662.04, "rate": Decimal("0.05")},           # 5%
        {"min": 118662.04, "max": 295654.82, "rate": Decimal("0.09")},   # 9%
        {"min": 295654.82, "max": 531176.65, "rate": Decimal("0.17")},   # 17%
        {"min": 531176.65, "max": 1062353.30, "rate": Decimal("0.23")},  # 23%
        {"min": 1062353.30, "max": float("inf"), "rate": Decimal("0.45")} # 45% top rate
    ]
    
    # CER values (Coeficiente de Estabilización de Referencia) - simplified
    # In production, this would be fetched from BCRA (Central Bank)
    CER_VALUES = {
        "2024-01": Decimal("1.0"),
        "2024-02": Decimal("1.015"),
        "2024-03": Decimal("1.032"),
        "2024-04": Decimal("1.050"),
        # ... more months would be added
    }
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate Ganancias (Capital Gains Tax)
        
        Argentina uses CER inflation adjustment and progressive rates
        
        Args:
            gains: List of capital gain transactions
            calculation_method: 'fifo', 'lifo', or 'average_cost'
        
        Returns:
            TaxCalculationResult with Ganancias calculation
        """
        total_gain = Decimal("0")
        cer_adjusted_gain = Decimal("0")
        
        # Apply CER adjustment to each gain
        for gain in gains:
            total_gain += gain.gain_amount
            
            # Get CER values for start and end months
            start_month = f"{gain.buy_date.year}-{gain.buy_date.month:02d}"
            end_month = f"{gain.sell_date.year}-{gain.sell_date.month:02d}"
            
            cer_start = self._get_cer_value(start_month)
            cer_end = self._get_cer_value(end_month)
            
            # Adjust gain: amount * (CER_final / CER_initial)
            if cer_start > 0:
                adjusted = gain.gain_amount * (cer_end / cer_start)
                cer_adjusted_gain += adjusted
        
        # Calculate Ganancias tax using progressive rates
        ganancias_tax = TaxCalculator.apply_progressive_rates(cer_adjusted_gain, self.GANANCIAS_RATES)
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="renta_financiera",
            tax_rate=self._calculate_average_rate(cer_adjusted_gain),
            calculated_tax=ganancias_tax,
            notes=f"CER-adjusted gain: {cer_adjusted_gain:.2f} ARS (original: {total_gain:.2f} ARS)"
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """
        Calculate Ganancias on ordinary income
        
        Staking, mining, airdrops taxed as ordinary income
        
        Args:
            income_amount: Total income amount in ARS
        
        Returns:
            TaxCalculationResult with Ganancias calculation
        """
        ganancias_tax = TaxCalculator.apply_progressive_rates(income_amount, self.GANANCIAS_RATES)
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="renta_ordinaria",
            tax_rate=self._calculate_average_rate(income_amount),
            calculated_tax=ganancias_tax,
            notes="Ganancias on staking/mining/airdrops income"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """
        Calculate IVA (Value Added Tax)
        
        21% standard IVA rate
        
        Args:
            transaction_value: Value of transaction
            transaction_type: Type of transaction
        
        Returns:
            TaxCalculationResult with IVA calculation
        """
        vat = Decimal("0")
        
        # Apply IVA on certain transactions
        if transaction_type in ["purchase", "service", "goods"]:
            vat = transaction_value * self.vat_rate
        
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="iva",
            tax_rate=self.vat_rate,
            calculated_tax=vat,
            notes="21% IVA (may be creditable if registered for IVA)"
        )
    
    def calculate_fee_deduction(
        self,
        fee_amount: Decimal
    ) -> Decimal:
        """
        Calculate deductible fees
        
        Trading and investment fees are deductible
        
        Args:
            fee_amount: Fee amount in ARS
        
        Returns:
            Deductible amount
        """
        return fee_amount
    
    def apply_progressive_rates(
        self,
        taxable_amount: Decimal
    ) -> Decimal:
        """
        Apply progressive Ganancias rates
        
        Args:
            taxable_amount: Taxable income amount
        
        Returns:
            Calculated Ganancias tax
        """
        return TaxCalculator.apply_progressive_rates(taxable_amount, self.GANANCIAS_RATES)
    
    def _get_cer_value(self, month_key: str) -> Decimal:
        """
        Get CER value for a specific month
        
        Args:
            month_key: Format YYYY-MM
        
        Returns:
            CER coefficient for that month
        """
        return self.CER_VALUES.get(month_key, Decimal("1.0"))
    
    def _calculate_average_rate(self, amount: Decimal) -> Decimal:
        """
        Calculate average tax rate for given amount
        
        Args:
            amount: Amount to calculate effective rate for
        
        Returns:
            Effective tax rate as percentage
        """
        if amount == 0:
            return Decimal("0")
        
        tax = TaxCalculator.apply_progressive_rates(amount, self.GANANCIAS_RATES)
        rate = (tax / amount * 100).quantize(Decimal("0.01"))
        return rate
    
    def get_form_requirements(self) -> Dict:
        """
        Get required tax forms for filing
        
        Returns:
            Dictionary of required forms
        """
        return {
            "primary_form": "DECLARACIÓN JURADA DE GANANCIAS",
            "schedules": [
                "F. 573 - Activos y Pasivos Exterior",
                "F. 1020 - Ganancia Impositiva",
                "F. 6 - Movimiento de capital"
            ],
            "required_docs": [
                "CUIT (Código Único de Identificación Tributaria)",
                "Proof of residence",
                "Brokerage statements",
                "CER adjustment documentation"
            ]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """
        Get tax filing deadline
        
        Argentina: May 15th of following year
        
        Args:
            year: Tax year
        
        Returns:
            Filing deadline as string
        """
        return f"May 15, {year + 1}"
    
    def apply_cer_adjustment(
        self,
        amount: Decimal,
        start_month: str,
        end_month: str
    ) -> Decimal:
        """
        Apply CER inflation adjustment
        
        Args:
            amount: Original amount
            start_month: Start month YYYY-MM
            end_month: End month YYYY-MM
        
        Returns:
            CER-adjusted amount
        """
        cer_start = self._get_cer_value(start_month)
        cer_end = self._get_cer_value(end_month)
        
        if cer_start == 0:
            return amount
        
        adjusted = amount * (cer_end / cer_start)
        return adjusted.quantize(Decimal("0.01"))
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "filing_frequency": "yearly",
            "filing_authority": "AFIP (Administración Federal de Ingresos Públicos)",
            "forms_required": self.get_form_requirements(),
            "special_feature": "CER inflation adjustment",
            "holding_period_days": self.holding_period_days
        }
