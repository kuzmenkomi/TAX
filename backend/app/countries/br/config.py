from decimal import Decimal
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict


class Brazil(SouthAmericaBase):
    """Brazil — Receita Federal 2026
    Sources:
      - MP 1.294/2025 + Lei 14.973/2024 (isenção R$ 5.000/mês in force Jan 2026)
      - Tabela Progressiva Mensal 2026 (DOU 27/12/2025)
      - IN RFB 2.121/2022  (crypto = bens e direitos, 15% CGT)
      - IN RFB 2.180/2024  (exchange reporting ≥ R$ 600/month from Jan 2026)
    Changes 2026: free threshold → R$ 3,036/month; isenção ampliada R$ 5k via restituição
    """
    country_code = "BR"
    country_name = "Brazil"
    currency = "BRL"
    currency_symbol = "R$"
    tax_authority = "Receita Federal"
    tax_authority_url = "https://www.gov.br/receitafederal"
    filing_deadline_full = "April 30"
    filing_deadline_month_day = "04-30"
    tax_year = 2026
    taxpayer_id_format = "CPF (11 digits)"
    taxpayer_id_regex = r"^\d{11}$"
    taxpayer_id_length = 11

    def get_tax_rates(self) -> Dict:
        """Tabela Progressiva Mensal 2026 (valores anualizados × 12)"""
        return {
            "income": [
                TaxBracket(0,                    Decimal("2259.20"),  Decimal("0")),
                TaxBracket(Decimal("2259.20"),   Decimal("2826.65"),  Decimal("0.075")),
                TaxBracket(Decimal("2826.65"),   Decimal("3751.05"),  Decimal("0.15")),
                TaxBracket(Decimal("3751.05"),   Decimal("4664.68"),  Decimal("0.225")),
                TaxBracket(Decimal("4664.68"),   float("inf"),        Decimal("0.275")),
            ],
            "capital_gains": Decimal("0.15"),
            "vat":           Decimal("0.18"),
            "crypto":        Decimal("0.15"),
            "dividends":     Decimal("0"),
            "staking_income":Decimal("0.15"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.20"), max_amount=Decimal("16754.35")),
            "health":       DeductionRule("health",       Decimal("1.00"), max_amount=float("inf")),
            "education":    DeductionRule("education",    Decimal("1.00"), max_amount=Decimal("3561.50")),
            "pension":      DeductionRule("pension",      Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "IRPF": TaxForm("IRPF", "Declaração Anual de Ajuste",            "April 30", True,  []),
            "DARF": TaxForm("DARF", "Guia de Recolhimento Mensal",            "Monthly",  False, ["has_crypto_gains_over_35k"]),
            "GCAP": TaxForm("GCAP", "Ganhos de Capital (programa Receita)",   "April 30", False, ["has_capital_gains"]),
            "DBE":  TaxForm("DBE",  "Declaração de Bens no Exterior",         "June 30",  False, ["has_foreign_assets_over_1M"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and len(taxpayer_id) == 11 and taxpayer_id.isdigit()

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"R$ {val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name,
            "region": self.country_region, "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority,
            "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full,
            "filing_frequency": "yearly", "fiscal_year": "calendar",
            "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains", "staking_treatment": "capital_gains",
            "exchange_reporting_threshold_brl": 600, "isencao_mensal_brl": 5000,
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Latin America", "LATAM Tax Network"],
        }
