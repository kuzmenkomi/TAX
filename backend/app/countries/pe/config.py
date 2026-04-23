from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Peru(SouthAmericaBase):
    """Peru Tax Jurisdiction - Impuesto a la Renta 2025/2026
    UIT 2025 = S/ 5,350 / UIT 2026 = S/ 5,550 (projected)
    Source: SUNAT / Ley del Impuesto a la Renta art. 53
    """
    country_code = "PE"
    country_name = "Peru"
    currency = "PEN"
    tax_authority = "SUNAT"
    filing_deadline_full = "April 15"
    
    # UIT 2026
    _UIT = Decimal("5550")
    
    def get_tax_rates(self) -> Dict:
        """Progressive rates per art. 53 Ley IR
        First 7 UIT are exempt, then progressive brackets in UIT multiples"""
        uit = self._UIT
        exempt = uit * 7  # S/ 38,850 exempt 
        return {
            "income": [
                TaxBracket(0,                       int(exempt),          Decimal("0")),      # Exempt (7 UIT)
                TaxBracket(int(exempt),              int(exempt + uit*5),  Decimal("0.08")),   # 8%  (next 5 UIT)
                TaxBracket(int(exempt + uit*5),      int(exempt + uit*20), Decimal("0.14")),   # 14% (next 15 UIT)
                TaxBracket(int(exempt + uit*20),     int(exempt + uit*35), Decimal("0.17")),   # 17% (next 15 UIT)
                TaxBracket(int(exempt + uit*35),     int(exempt + uit*45), Decimal("0.20")),   # 20% (next 10 UIT)
                TaxBracket(int(exempt + uit*45),     float("inf"),         Decimal("0.30")),   # 30% (excess)
            ],
            "capital_gains": Decimal("0.05"),   # 5% for securities / 30% for others
            "vat": Decimal("0.18"),             # IGV
            "crypto": Decimal("0.30"),          # Treated as ordinary income
            "dividends": Decimal("0.05"),       # 5% for residents
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.20"), max_amount=float('inf')),
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "AFP": DeductionRule("AFP", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "709": TaxForm("709", "Annual Income Tax Return", "April 15", True, []),
            "621": TaxForm("621", "Monthly IGV-Renta", "Monthly", False, ["has_business_income"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate RUC (11 digits) or DNI (8 digits)"""
        if not taxpayer_id:
            return False
        return taxpayer_id.isdigit() and (len(taxpayer_id) == 8 or len(taxpayer_id) == 11)
    
    def format_currency(self, amount: Decimal) -> str:
        return f"S/. {amount:,.2f}"
    
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
            "currency_symbol": "S/.",
        }
