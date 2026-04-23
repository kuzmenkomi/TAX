from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Ecuador(SouthAmericaBase):
    """Ecuador Tax Jurisdiction - Impuesto a la Renta 2025
    Source: SRI Resolución No. NAC-DGERCGC24-00000041
    """
    country_code = "EC"
    country_name = "Ecuador"
    currency = "USD"
    tax_authority = "SRI"
    filing_deadline_full = "March 28"
    
    def get_tax_rates(self) -> Dict:
        """Progressive income tax rates for individuals (2025)
        10 brackets up to 37%"""
        return {
            "income": [
                TaxBracket(0, Decimal("12081"), Decimal("0")),                     # 0%
                TaxBracket(Decimal("12081"), Decimal("15387"), Decimal("0.05")),   # 5%
                TaxBracket(Decimal("15387"), Decimal("19978"), Decimal("0.10")),   # 10%
                TaxBracket(Decimal("19978"), Decimal("26422"), Decimal("0.12")),   # 12%
                TaxBracket(Decimal("26422"), Decimal("34770"), Decimal("0.15")),   # 15%
                TaxBracket(Decimal("34770"), Decimal("46089"), Decimal("0.20")),   # 20%
                TaxBracket(Decimal("46089"), Decimal("61359"), Decimal("0.25")),   # 25%
                TaxBracket(Decimal("61359"), Decimal("81817"), Decimal("0.30")),   # 30%
                TaxBracket(Decimal("81817"), Decimal("108810"), Decimal("0.35")),  # 35%
                TaxBracket(Decimal("108810"), float("inf"), Decimal("0.37")),      # 37%
            ],
            "capital_gains": Decimal("0.10"),   # Generally 10% on share transfers
            "vat": Decimal("0.15"),             # IVA increased in 2024
            "crypto": Decimal("0.37"),          # Treated as ordinary income if frequent
            "dividends": Decimal("0.10"),       # Retenidos en la fuente
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.20"), max_amount=float('inf')),
            "personal_expenses": DeductionRule("personal_expenses", Decimal("1.00"), max_amount=Decimal("15294")), # Varies by family size, approx value
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "102": TaxForm("102", "Annual Income Declaration (Personas Naturales)", "March", True, []),
            "104": TaxForm("104", "IVA Declaration", "Monthly/Semestral", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate RUC (13 digits) or Cédula (10 digits)"""
        if not taxpayer_id:
            return False
        return taxpayer_id.isdigit() and (len(taxpayer_id) == 10 or len(taxpayer_id) == 13)
    
    def format_currency(self, amount: Decimal) -> str:
        return f"${amount:,.2f} USD"
    
    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code,
            "name": self.country_name,
            "currency": self.currency,
            "tax_authority": self.tax_authority,
            "filing_frequency": "yearly",
            "fiscal_year": "calendar",
            "holding_period_distinction": False,
            "vat_applicable": True,
            "crypto_treatment": "ordinary_income",
            "api_available": True,
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
            "region": "South America",
            "currency_symbol": "$",
        }
