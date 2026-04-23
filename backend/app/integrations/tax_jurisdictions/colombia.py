"""
Colombia Tax Jurisdiction Implementation
Impuesto a la Renta (Income Tax) + IVA
"""
from typing import List, Dict
from decimal import Decimal
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class ColombiaTaxJurisdiction(BaseTaxJurisdiction):
    """
    Colombia tax jurisdiction
    - Renta: Progressive income tax (0% - 39%)
    - UVT-based thresholds (Unidad de Valor Tributario)
    - Capital Gains: 10% special rate
    - IVA: 19% standard VAT
    - Crypto: Otros ingresos y ganancias ocasionales
    """
    
    code = "CO"
    name = "Colombia"
    currency = "COP"
    vat_rate = Decimal("0.19")  # 19% IVA
    tax_rate = Decimal("0.15")  # Average income tax
    holding_period_days = 365
    
    # UVT 2024: 43,628 COP (updates yearly)
    UVT_2024 = Decimal("43628")
    
    # Renta Progressive rates
    RENTA_RATES = [
        {"min": 0, "max": 95, "rate": Decimal("0")},              # 0-95 UVT: 0%
        {"min": 95, "max": 150, "rate": Decimal("0.19")},         # 95-150 UVT: 19%
        {"min": 150, "max": 360, "rate": Decimal("0.28")},        # 150-360 UVT: 28%
        {"min": 360, "max": 816, "rate": Decimal("0.33")},        # 360-816 UVT: 33%
        {"min": 816, "max": float("inf"), "rate": Decimal("0.39")} # 816+ UVT: 39%
    ]
    
    # Capital Gains Tax
    CAPITAL_GAINS_RATE = Decimal("0.10")  # 10% flat rate
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate capital gains tax
        
        Colombia has 10% flat tax for capital gains
        
        Args:
            gains: List of capital gain transactions
            calculation_method: 'fifo', 'lifo', or 'average_cost'
        
        Returns:
            TaxCalculationResult
        """
        total_gain = TaxCalculator.calculate_total_gain(gains)
        capital_gains_tax = total_gain * self.CAPITAL_GAINS_RATE
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="ganancias_ocasionales",
            tax_rate=self.CAPITAL_GAINS_RATE,
            calculated_tax=capital_gains_tax,
            notes="10% flat tax on capital gains"
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """Calculate income tax using progressive rates"""
        # Convert to UVT units
        income_uvt = income_amount / self.UVT_2024
        
        renta_tax = TaxCalculator.apply_progressive_rates(income_uvt, self.RENTA_RATES)
        # Convert back to COP
        renta_tax_cop = renta_tax * self.UVT_2024
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="renta_ordinaria",
            tax_rate=Decimal(str(renta_tax / income_uvt * 100)) if income_uvt > 0 else Decimal("0"),
            calculated_tax=renta_tax_cop,
            notes=f"Progressive tax based on {income_uvt:.2f} UVT"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """Calculate IVA"""
        vat = transaction_value * self.vat_rate if transaction_type in ["purchase", "service"] else Decimal("0")
        
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="iva",
            tax_rate=self.vat_rate,
            calculated_tax=vat,
            notes="19% IVA"
        )
    
    def calculate_fee_deduction(self, fee_amount: Decimal) -> Decimal:
        """Calculate deductible fees"""
        return fee_amount
    
    def apply_progressive_rates(self, taxable_amount: Decimal) -> Decimal:
        """Apply progressive Renta rates"""
        income_uvt = taxable_amount / self.UVT_2024
        tax = TaxCalculator.apply_progressive_rates(income_uvt, self.RENTA_RATES)
        return tax * self.UVT_2024
    
    def get_form_requirements(self) -> Dict:
        """Get required tax forms"""
        return {
            "primary_form": "DECLARACIÓN DE RENTA Y COMPLEMENTARIOS",
            "schedules": ["Renta líquida cédula", "Anexo de patrimonio"],
            "required_docs": ["NIT", "Proof of residence", "Bank statements"]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """Get filing deadline - Colombia: Variable by NIT"""
        return f"March-April {year + 1} (varies by NIT last digit)"
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "filing_frequency": "yearly",
            "filing_authority": "DIAN (Dirección de Impuestos y Aduanas Nacionales)",
            "forms_required": self.get_form_requirements(),
            "holding_period_days": self.holding_period_days
        }
