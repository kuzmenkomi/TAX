"""
Peru Tax Jurisdiction Implementation
Impuesto a la Renta (IR) + IGV
"""
from typing import List, Dict
from decimal import Decimal
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class PeruTaxJurisdiction(BaseTaxJurisdiction):
    """
    Peru tax jurisdiction
    - IR: 30% flat rate for individuals (Tercera categoría)
    - UIT adjustment (Unidad Impositiva Tributaria)
    - IGV: 18% VAT
    - Crypto: Rentas de tercera categoría
    - Forms: Formulario 710-B (Patrimonio), Anexo A (Ingresos)
    """
    
    code = "PE"
    name = "Peru"
    currency = "PEN"
    vat_rate = Decimal("0.18")  # 18% IGV
    tax_rate = Decimal("0.30")  # 30% flat income tax
    holding_period_days = 365
    
    # IR rates for individuals
    IR_RATE = Decimal("0.30")  # 30% for tercera categoría
    
    # UIT 2024: 5,150 PEN
    UIT_2024 = Decimal("5150")
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate capital gains tax
        
        Peru: 30% on gains from sales of crypto
        
        Args:
            gains: List of capital gain transactions
            calculation_method: Calculation method
        
        Returns:
            TaxCalculationResult
        """
        total_gain = TaxCalculator.calculate_total_gain(gains)
        ir_tax = total_gain * self.IR_RATE
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="renta_tercera_categoria",
            tax_rate=self.IR_RATE,
            calculated_tax=ir_tax,
            notes="30% IR on capital gains"
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """Calculate income tax"""
        ir_tax = income_amount * self.IR_RATE
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="renta_tercera_categoria",
            tax_rate=self.IR_RATE,
            calculated_tax=ir_tax,
            notes="30% IR on income"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """Calculate IGV"""
        igv = transaction_value * self.vat_rate if transaction_type in ["purchase", "service"] else Decimal("0")
        
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="igv",
            tax_rate=self.vat_rate,
            calculated_tax=igv,
            notes="18% IGV"
        )
    
    def calculate_fee_deduction(self, fee_amount: Decimal) -> Decimal:
        """Calculate deductible fees"""
        return fee_amount
    
    def apply_progressive_rates(self, taxable_amount: Decimal) -> Decimal:
        """Apply IR (flat 30%)"""
        return taxable_amount * self.IR_RATE
    
    def get_form_requirements(self) -> Dict:
        """Get required tax forms"""
        return {
            "primary_form": "DECLARACIÓN DE IMPUESTO A LA RENTA",
            "schedules": ["F. 710-B (Patrimonio)", "Anexo A (Ingresos)"],
            "required_docs": ["RUC (Registro Único de Contribuyente)", "Bank statements"]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """Get filing deadline - Peru: March 31st"""
        return f"March 31, {year + 1}"
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "income_tax_rate": float(self.IR_RATE),
            "filing_frequency": "yearly",
            "filing_authority": "SUNAT (Superintendencia Nacional de Aduanas y de Administración Tributaria)",
            "forms_required": self.get_form_requirements(),
            "holding_period_days": self.holding_period_days
        }
