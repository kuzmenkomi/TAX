from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm
from typing import Dict

class CostaRica(BaseCountryDefinition):
    """Costa Rica Tax Jurisdiction - Income Tax + VAT"""
    country_code = "CR"
    country_name = "Costa Rica"
    currency = "CRC"
    tax_authority = "Hacienda"
    filing_deadline_full = "April 15"
    region = "Central America"
    
    def get_tax_rates(self) -> Dict:
        """Costa Rica Income Tax 2025 Tranches (Salaried Employees)"""
        return {
            "income": [
                TaxBracket(0, 11292000, Decimal("0")),
                TaxBracket(11292000, 16572000, Decimal("0.10")),
                TaxBracket(16572000, 29064000, Decimal("0.15")),
                TaxBracket(29064000, 58140000, Decimal("0.20")),
                TaxBracket(58140000, float("inf"), Decimal("0.25")),
            ],
            "capital_gains": Decimal("0.15"),
            "vat": Decimal("0.13"),
            "crypto": Decimal("0.15"),
            "dividends": Decimal("0.15"),
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.10"), max_amount=float('inf')),
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "charitable": DeductionRule("charitable", Decimal("0.10"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "D101": TaxForm("D101", "Annual Return", "April 15", True, []),
            "D104": TaxForm("D104", "Conditional Income", "April 15", False, ["has_dividends"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate Cédula (10 chars: X-XXXX-XXXX format)"""
        if not taxpayer_id:
            return False
        # Remove hyphens if present
        taxpayer_id = taxpayer_id.replace("-", "")
        return len(taxpayer_id) == 10 and taxpayer_id.isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"₡{amount:,.2f}"
    
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
            "api_available": False,
            "regions": ["Central America", "LATAM Tax Network"],
            "region": "Central America",
            "currency_symbol": "₡",
        }
