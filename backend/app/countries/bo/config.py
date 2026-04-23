from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Bolivia(SouthAmericaBase):
    """Bolivia Tax Jurisdiction - RC-IVA (Flat 13%)
    Bolivia does not have a progressive income tax for individuals.
    It uses a flat 13% rate (RC-IVA) which can be offset with invoices.
    """
    country_code = "BO"
    country_name = "Bolivia"
    currency = "BOB"
    tax_authority = "SIN"
    filing_deadline_full = "Quarterly/Monthly"
    
    def get_tax_rates(self) -> Dict:
        """Flat 13% for RC-IVA, not progressive."""
        return {
            "income": [
                TaxBracket(0, float("inf"), Decimal("0.13")), # Flat 13% RC-IVA
            ],
            "capital_gains": Decimal("0.13"),   # Handled similarly via RC-IVA/IT
            "vat": Decimal("0.13"),             # Nominal IVA 13% (effective 14.94%)
            "crypto": Decimal("0.13"),
            "dividends": Decimal("0.13"),       # RC-IVA on dividends
        }
    
    def get_deductions(self) -> Dict:
        """In Bolivia, deductions are primarily via Fiscal Invoices (Facturas)
        to credit against the RC-IVA. Also 13% of minimum national wages.
        """
        return {
            "invoice_credit": DeductionRule("invoice_credit", Decimal("1.00"), max_amount=float('inf')), # 13% of invoice values
            "minimum_wage_allowance": DeductionRule("minimum_wage_allowance", Decimal("1.00"), max_amount=float('inf')), # Deduction of minimum wages
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "Form-610": TaxForm("Form-610", "Quarterly RC-IVA", "Quarterly", True, []),
            "Form-110": TaxForm("Form-110", "Detail of invoices", "Quarterly/Monthly", False, ["has_deductions"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate NIT (10-13 digits)"""
        if not taxpayer_id:
            return False
        return taxpayer_id.isdigit() and 10 <= len(taxpayer_id) <= 13
    
    def format_currency(self, amount: Decimal) -> str:
        return f"Bs. {amount:,.2f}"
    
    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code,
            "name": self.country_name,
            "currency": self.currency,
            "tax_authority": self.tax_authority,
            "filing_frequency": "quarterly", # RC-IVA independent is quarterly
            "fiscal_year": "calendar",
            "holding_period_distinction": False,
            "vat_applicable": True,
            "crypto_treatment": "rc_iva",
            "api_available": False,
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
            "region": "South America",
            "currency_symbol": "Bs.",
        }
