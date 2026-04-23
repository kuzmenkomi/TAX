from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Chile(SouthAmericaBase):
    """Chile Tax Jurisdiction - Income Tax + IVA"""
    country_code = "CL"
    country_name = "Chile"
    currency = "CLP"
    tax_authority = "SII"
    filing_deadline_full = "April 30"
    
    def get_tax_rates(self) -> Dict:
        """Chile IGC (Individual Global Complementary) 2025 Brackets"""
        uta = Decimal("790000") # Projected 2025 UTA anchor
        return {
            "income": [
                TaxBracket(0, uta * Decimal("13.5"), Decimal("0")),
                TaxBracket(uta * Decimal("13.5"), uta * Decimal("30"), Decimal("0.04")),
                TaxBracket(uta * Decimal("30"), uta * Decimal("50"), Decimal("0.08")),
                TaxBracket(uta * Decimal("50"), uta * Decimal("70"), Decimal("0.135")),
                TaxBracket(uta * Decimal("70"), uta * Decimal("90"), Decimal("0.23")),
                TaxBracket(uta * Decimal("90"), uta * Decimal("120"), Decimal("0.304")),
                TaxBracket(uta * Decimal("120"), uta * Decimal("310"), Decimal("0.35")),
                TaxBracket(uta * Decimal("310"), float("inf"), Decimal("0.40")),
            ],
            "capital_gains": Decimal("0.10"),   # Reduced rate for certain assets/instruments
            "vat": Decimal("0.19"),             # Standard IVA
            "crypto": Decimal("0.20"),          # Treated as non-qualified capital gains
            "dividends": Decimal("0.07"),       # Withholding for residents
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.10"), max_amount=float('inf')),
            "health": DeductionRule("health", Decimal("0.07"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "pension": DeductionRule("pension", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "F22": TaxForm("F22", "Annual Income Tax Return", "April 30", True, []),
            "F29": TaxForm("F29", "VAT Declaration", "Monthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate RUN (9-10 chars with verification digit)"""
        if not taxpayer_id or len(taxpayer_id) < 9 or len(taxpayer_id) > 10:
            return False
        return taxpayer_id[:-1].isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"${amount:,.0f} CLP"
    
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
            "crypto_treatment": "capital_gains",
            "api_available": True,
            "regions": ["South America", "Southern Cone", "LATAM Tax Network"],
            "region": "South America",
            "currency_symbol": "$",
        }
