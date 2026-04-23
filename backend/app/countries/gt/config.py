# Guatemala Tax Configuration
# Decreto 10-2012 (Ley de Actualización Tributaria)
# SAT (Superintendencia de Administración Tributaria)

from decimal import Decimal
from typing import Dict
from app.countries.base import CentralAmericaBase, TaxBracket, DeductionRule, TaxForm


class Guatemala(CentralAmericaBase):
    """
    Guatemala tax configuration 2025/2026.
    Decreto 10-2012 - Ley de Actualización Tributaria
    - Currency: Quetzal (GTQ)
    - Tax Authority: SAT
    - Main tax: ISR (employees: 5%/7% progressive)
    - Filing deadline: March 31
    """

    country_code = "GT"
    country_name = "Guatemala"
    currency = "GTQ"
    tax_authority = "SAT"
    filing_deadline_full = "March 31"
    
    def get_tax_rates(self) -> Dict:
        """ISR rates for employees (Decreto 10-2012 art. 73):
        - 5% on first Q300,000 of taxable income
        - 7% on the excess over Q300,000
        Capital gains: 10% (art. 84)
        Dividends: 5% (art. 93)
        IVA: 12%"""
        return {
            "income": [
                TaxBracket(0, Decimal("48000"), Decimal("0")),               # Q48,000 personal deduction (exempt)
                TaxBracket(Decimal("48000"), Decimal("300000"), Decimal("0.05")),  # 5%
                TaxBracket(Decimal("300000"), float("inf"), Decimal("0.07")),      # 7%
            ],
            "capital_gains": Decimal("0.10"),   # 10% on capital gains
            "vat": Decimal("0.12"),             # IVA 12%
            "crypto": Decimal("0.10"),          # Treated as capital gain
            "dividends": Decimal("0.05"),       # 5% on dividends
        }
    
    def get_deductions(self) -> Dict:
        """Deductions for Guatemala - up to Q48,000 personal deduction"""
        return {
            "personal": DeductionRule("personal", Decimal("1.00"), max_amount=Decimal("48000")),
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "charitable": DeductionRule("charitable", Decimal("0.05"), max_amount=Decimal("500000")),
            "social_security": DeductionRule("social_security", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        """Required tax forms"""
        return {
            "SAT-1411": TaxForm("SAT-1411", "ISR Annual Declaration", "March 31", True, []),
            "SAT-2237": TaxForm("SAT-2237", "IVA Monthly", "Monthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate NIT (7-9 digits + check digit, or full format)"""
        if not taxpayer_id:
            return False
        cleaned = taxpayer_id.replace("-", "").replace(" ", "")
        return len(cleaned) >= 7 and len(cleaned) <= 13 and cleaned.isdigit()
    
    def format_currency(self, amount) -> str:
        """Format in GTQ"""
        return f"Q {amount:,.2f}"
    
    def get_country_info(self) -> Dict:
        """Country information"""
        return {
            "code": self.country_code,
            "name": self.country_name,
            "currency": self.currency,
            "currency_symbol": "Q",
            "tax_authority": self.tax_authority,
            "api_available": True,
            "region": "Central America",
            "regions": ["Central America", "Latin America", "LATAM Tax Network"],
        }
