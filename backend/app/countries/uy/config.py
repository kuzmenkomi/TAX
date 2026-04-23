from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Uruguay(SouthAmericaBase):
    """Uruguay Tax Jurisdiction - Income Tax + IVA"""
    country_code = "UY"
    country_name = "Uruguay"
    currency = "UYU"
    tax_authority = "DGI"
    filing_deadline_full = "April 30"
    
    def get_tax_rates(self) -> Dict:
        """Uruguay IRPF 2025 Brackets (Progressive Monthly converted to Annual)"""
        bpc = Decimal("6550") # Base de Prestaciones y Contribuciones 2025
        return {
            "income": [
                TaxBracket(0, bpc * Decimal("84"), Decimal("0")),
                TaxBracket(bpc * Decimal("84"), bpc * Decimal("120"), Decimal("0.10")),
                TaxBracket(bpc * Decimal("120"), bpc * Decimal("180"), Decimal("0.15")),
                TaxBracket(bpc * Decimal("180"), bpc * Decimal("360"), Decimal("0.24")),
                TaxBracket(bpc * Decimal("360"), bpc * Decimal("600"), Decimal("0.25")),
                TaxBracket(bpc * Decimal("600"), bpc * Decimal("900"), Decimal("0.27")),
                TaxBracket(bpc * Decimal("900"), bpc * Decimal("1380"), Decimal("0.31")),
                TaxBracket(bpc * Decimal("1380"), float("inf"), Decimal("0.36")),
            ],
            "capital_gains": Decimal("0.12"),
            "vat": Decimal("0.22"),
            "crypto": Decimal("0.12"),
            "dividends": Decimal("0.07"),
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.10"), max_amount=float('inf')),
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "pension": DeductionRule("pension", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "M3": TaxForm("M3", "Annual Return", "April 30", True, []),
            "IVA": TaxForm("IVA", "Monthly VAT", "Monthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate CI (8 digits) or RUT (12 digits)"""
        if not taxpayer_id:
            return False
        return taxpayer_id.isdigit() and (len(taxpayer_id) == 8 or len(taxpayer_id) == 12)
    
    def format_currency(self, amount: Decimal) -> str:
        return f"${amount:,.2f} UYU"
    
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
            "currency_symbol": "$U",
        }
