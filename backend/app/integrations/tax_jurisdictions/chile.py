"""
Chile Tax Jurisdiction Implementation
Impuesto Global Complementario + Impuesto Adicional
"""
from typing import List, Dict
from decimal import Decimal
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator


class ChileTaxJurisdiction(BaseTaxJurisdiction):
    """
    Chile tax jurisdiction
    - IGC: Global Complementary Tax (Progressive 0% - 37%)
    - IA: Additional Tax (35% for non-residents)
    - Capital Gains: Included in income
    - IVA: 19% VAT
    - Crypto: Renta de fuente extranjera
    - Forms: Formulario 1880 (Declaration), F-14 (Capital gains), F-22 (VAT)
    """
    
    code = "CL"
    name = "Chile"
    currency = "CLP"
    vat_rate = Decimal("0.19")  # 19% IVA
    tax_rate = Decimal("0.20")  # Average income tax
    holding_period_days = 365
    
    # IGC Progressive rates 2024
    IGC_RATES = [
        {"min": 0, "max": 13.5, "rate": Decimal("0")},               # 0-13.5 UTA: 0%
        {"min": 13.5, "max": 30, "rate": Decimal("0.05")},           # 13.5-30 UTA: 5%
        {"min": 30, "max": 50, "rate": Decimal("0.10")},             # 30-50 UTA: 10%
        {"min": 50, "max": 60, "rate": Decimal("0.14")},             # 50-60 UTA: 14%
        {"min": 60, "max": 70, "rate": Decimal("0.17")},             # 60-70 UTA: 17%
        {"min": 70, "max": 80, "rate": Decimal("0.20")},             # 70-80 UTA: 20%
        {"min": 80, "max": 90, "rate": Decimal("0.23")},             # 80-90 UTA: 23%
        {"min": 90, "max": 200, "rate": Decimal("0.30")},            # 90-200 UTA: 30%
        {"min": 200, "max": float("inf"), "rate": Decimal("0.37")}   # 200+ UTA: 37%
    ]
    
    # UTA 2024: 537,005 CLP
    UTA_2024 = Decimal("537005")
    
    # Additional Tax for non-residents
    ADDITIONAL_TAX_RATE = Decimal("0.35")  # 35%
    
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate capital gains tax
        
        Chile: Capital gains taxed as income using IGC rates
        
        Args:
            gains: List of capital gain transactions
            calculation_method: Calculation method
        
        Returns:
            TaxCalculationResult
        """
        total_gain = TaxCalculator.calculate_total_gain(gains)
        
        # Convert to UTA and apply rates
        gain_uta = total_gain / self.UTA_2024
        igc_tax = TaxCalculator.apply_progressive_rates(gain_uta, self.IGC_RATES)
        igc_tax_clp = igc_tax * self.UTA_2024
        
        return TaxCalculationResult(
            transaction_type="capital_gains",
            amount=total_gain,
            tax_category="renta_extranjera",
            tax_rate=Decimal(str(igc_tax / gain_uta * 100)) if gain_uta > 0 else Decimal("0"),
            calculated_tax=igc_tax_clp,
            notes=f"IGC progressive tax on {gain_uta:.3f} UTA"
        )
    
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """Calculate income tax using IGC rates"""
        income_uta = income_amount / self.UTA_2024
        igc_tax = TaxCalculator.apply_progressive_rates(income_uta, self.IGC_RATES)
        igc_tax_clp = igc_tax * self.UTA_2024
        
        return TaxCalculationResult(
            transaction_type="income",
            amount=income_amount,
            tax_category="renta_ordinaria",
            tax_rate=Decimal(str(igc_tax / income_uta * 100)) if income_uta > 0 else Decimal("0"),
            calculated_tax=igc_tax_clp,
            notes=f"IGC progressive tax on {income_uta:.3f} UTA"
        )
    
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """Calculate IVA"""
        iva = transaction_value * self.vat_rate if transaction_type in ["purchase", "service"] else Decimal("0")
        
        return TaxCalculationResult(
            transaction_type="vat",
            amount=transaction_value,
            tax_category="iva",
            tax_rate=self.vat_rate,
            calculated_tax=iva,
            notes="19% IVA"
        )
    
    def calculate_fee_deduction(self, fee_amount: Decimal) -> Decimal:
        """Calculate deductible fees"""
        return fee_amount
    
    def apply_progressive_rates(self, taxable_amount: Decimal) -> Decimal:
        """Apply IGC progressive rates"""
        amount_uta = taxable_amount / self.UTA_2024
        tax = TaxCalculator.apply_progressive_rates(amount_uta, self.IGC_RATES)
        return tax * self.UTA_2024
    
    def calculate_additional_tax_non_resident(
        self,
        income_amount: Decimal
    ) -> Decimal:
        """
        Calculate additional tax for non-residents
        
        35% tax on Chilean-source income for non-residents
        
        Args:
            income_amount: Income amount
        
        Returns:
            Calculated additional tax
        """
        return income_amount * self.ADDITIONAL_TAX_RATE
    
    def get_form_requirements(self) -> Dict:
        """Get required tax forms"""
        return {
            "primary_form": "FORMULARIO 1880 - DECLARACIÓN DE RENTA",
            "schedules": [
                "F-14 (Capital gains)",
                "F-22 (Monthly VAT reporting)",
                "F-29 (Monthly income tax)"
            ],
            "required_docs": ["RUN (Rol Único Nacional)", "Bank statements"]
        }
    
    def get_filing_deadline(self, year: int) -> str:
        """Get filing deadline - Chile: April 30th"""
        return f"April 30, {year + 1}"
    
    def get_jurisdiction_info(self) -> Dict:
        """Get jurisdiction information"""
        return {
            "code": self.code,
            "name": self.name,
            "currency": self.currency,
            "vat_rate": float(self.vat_rate),
            "filing_frequency": "yearly",
            "filing_authority": "SII (Servicio de Impuestos Internos)",
            "forms_required": self.get_form_requirements(),
            "holding_period_days": self.holding_period_days,
            "special_feature": "UTA-based progressive rates"
        }
