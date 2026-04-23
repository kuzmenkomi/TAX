# Base Tax Calculator - inherited by all countries
# Provides common tax calculation logic

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.countries.base.definitions import (
    BaseCountryDefinition,
    TaxType,
    TaxBracket,
    DeductionRule,
)
from app.services.financial_data_service import FinancialDataService
from decimal import Decimal


class BaseTaxCalculator(ABC):
    """
    Abstract base class for all country tax calculators.
    
    Provides:
    - Progressive tax calculation
    - Deduction application
    - Capital gains handling
    - Multi-asset tax computation
    
    Each country overrides specific methods for jurisdiction rules.
    """

    def __init__(self, country_def: BaseCountryDefinition):
        """
        Initialize calculator with country definition.
        
        Args:
            country_def: Country definition instance
        """
        self.country = country_def
        self._cache: Dict[str, Any] = {}

    def calculate_income_tax(
        self,
        gross_income: float,
        deductions: Dict[str, float] = None,
        filing_status: str = "single",
    ) -> Dict[str, Any]:
        """
        Calculate income tax for the country.
        
        Base implementation handles progressive taxation.
        Override for country-specific rules.
        
        Args:
            gross_income: Total income before deductions
            deductions: Mapping of deduction categories to amounts
            filing_status: "single", "married", etc.
            
        Returns:
            {
                "gross_income": 50000,
                "total_deductions": 5000,
                "taxable_income": 45000,
                "income_tax": 6750,
                "effective_rate": 0.135,
                "deduction_breakdown": {...},
            }
        """
        deductions = deductions or {}

        # Calculate total deductions
        total_deductions = sum(deductions.values())
        taxable_income = max(0, gross_income - total_deductions)

        # Calculate tax using progressive brackets
        tax_breakdown = self.country.calculate_progressive_tax(
            taxable_income,
            TaxType.INCOME_TAX,
        )

        income_tax = tax_breakdown["gross_tax"]

        return {
            "gross_income": gross_income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "effective_rate": income_tax / gross_income if gross_income > 0 else 0,
            "deduction_breakdown": deductions,
            "tax_breakdown": tax_breakdown,
        }

    def calculate_capital_gains_tax(
        self,
        capital_gains: float,
        holding_period_days: int = 365,
    ) -> Dict[str, Any]:
        """
        Calculate capital gains tax.
        
        Base implementation treats all gains same.
        Override for short-term vs long-term rules.
        
        Args:
            capital_gains: Amount of capital gains
            holding_period_days: How long asset was held
            
        Returns:
            {
                "capital_gains": 10000,
                "holding_period_days": 365,
                "gain_type": "long_term",
                "capital_gains_tax": 3100,
                "effective_rate": 0.31,
            }
        """
        # Determine gain type based on holding period
        gain_type = "long_term" if holding_period_days >= 365 else "short_term"

        # Calculate tax
        tax_breakdown = self.country.calculate_progressive_tax(
            capital_gains,
            TaxType.CAPITAL_GAINS,
        )

        return {
            "capital_gains": capital_gains,
            "holding_period_days": holding_period_days,
            "gain_type": gain_type,
            "capital_gains_tax": tax_breakdown["gross_tax"],
            "effective_rate": tax_breakdown["effective_rate"],
        }

    def calculate_cryptocurrency_tax(
        self,
        crypto_gains: float = 0,
        staking_income: float = 0,
        mining_income: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tax on cryptocurrency transactions.
        
        Base treats crypto as capital gains.
        Override for country-specific crypto rules.
        
        Args:
            crypto_gains: Gains from trading
            staking_income: Income from staking/validation
            mining_income: Income from mining
            
        Returns:
            Crypto tax breakdown
        """
        total_crypto_income = crypto_gains + staking_income + mining_income

        # Treat each component
        tax_breakdown = {
            "crypto_gains": self.calculate_capital_gains_tax(crypto_gains),
            "staking_income": self.calculate_income_tax(staking_income),
            "mining_income": self.calculate_income_tax(mining_income),
        }

        total_tax = (
            tax_breakdown["crypto_gains"]["capital_gains_tax"]
            + tax_breakdown["staking_income"]["income_tax"]
            + tax_breakdown["mining_income"]["income_tax"]
        )

        return {
            "total_crypto_income": total_crypto_income,
            "components": tax_breakdown,
            "total_cryptocurrency_tax": total_tax,
        }

    def calculate_defi_tax(
        self,
        farming_income: float = 0,
        yield_income: float = 0,
        swap_gains: float = 0,
        liquidity_pool_gains: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tax on DeFi activities.
        
        Base treats DeFi income as capital gains.
        Override for country-specific DeFi rules.
        """
        total_defi_income = farming_income + yield_income + swap_gains

        return {
            "farming_income": farming_income,
            "yield_income": yield_income,
            "swap_gains": swap_gains,
            "liquidity_pool_gains": liquidity_pool_gains,
            "total_defi_income": total_defi_income,
            "farming_tax": self.calculate_income_tax(farming_income),
            "yield_tax": self.calculate_income_tax(yield_income),
            "swap_tax": self.calculate_capital_gains_tax(swap_gains),
            "lp_tax": self.calculate_capital_gains_tax(liquidity_pool_gains),
        }

    def convert_to_local_currency(self, amount: float, from_currency: str) -> float:
        """
        Convert an amount from a foreign currency to the local currency.
        
        Args:
            amount: Amount in foreign currency
            from_currency: ISO currency code (USD, BTC, etc.)
            
        Returns:
            Amount in local currency
        """
        if from_currency.upper() == self.country.currency.upper():
            return amount
            
        rate = FinancialDataService.get_exchange_rate(from_currency.upper(), self.country.currency.upper())
        return float(Decimal(str(amount)) * rate)

    def calculate_total_tax_liability(
        self,
        gross_income: float = 0,
        capital_gains: float = 0,
        crypto_activity: Dict[str, float] = None,
        defi_activity: Dict[str, float] = None,
        deductions: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total tax liability across all income types.
        
        Args:
            gross_income: Regular employment income
            capital_gains: Gains from asset sales
            crypto_activity: Dict with crypto components
            defi_activity: Dict with DeFi components
            deductions: Available deductions
            
        Returns:
            Complete tax liability breakdown
        """
        crypto_activity = crypto_activity or {}
        defi_activity = defi_activity or {}
        deductions = deductions or {}

        # Calculate each component
        income_tax = self.calculate_income_tax(gross_income, deductions)
        cap_gains_tax = self.calculate_capital_gains_tax(capital_gains)
        crypto_tax = self.calculate_cryptocurrency_tax(**crypto_activity)
        defi_tax = self.calculate_defi_tax(**defi_activity)

        # Calculate VAT if applicable (on transactions)
        vat_tax = self._calculate_vat(
            gross_income + capital_gains + crypto_activity.get("crypto_gains", 0)
        )

        # Total tax — sum actual computed taxes, not raw income
        defi_tax_total = (
            defi_tax["farming_tax"]["income_tax"]
            + defi_tax["yield_tax"]["income_tax"]
            + defi_tax["swap_tax"]["capital_gains_tax"]
            + defi_tax["lp_tax"]["capital_gains_tax"]
        )
        total_tax = (
            income_tax["income_tax"]
            + cap_gains_tax["capital_gains_tax"]
            + crypto_tax["total_cryptocurrency_tax"]
            + defi_tax_total
            + vat_tax
        )

        return {
            "country": self.country.country_name,
            "tax_year": self.country.tax_year,
            "currency": self.country.currency,
            "components": {
                "income_tax": income_tax,
                "capital_gains_tax": cap_gains_tax,
                "cryptocurrency_tax": crypto_tax,
                "defi_tax": defi_tax,
                "vat_tax": vat_tax,
            },
            "total_tax_liability": total_tax,
            "effective_tax_rate": total_tax / (gross_income + capital_gains) if (gross_income + capital_gains) > 0 else 0,
        }

    def _calculate_vat(self, taxable_amount: float) -> float:
        """Calculate VAT if applicable in the country"""
        rates = self.country.get_tax_rates()
        # Handle both Enum and string keys for robustness
        vat_data = rates.get(TaxType.VAT) or rates.get("vat")
        
        if not vat_data:
            return 0.0
        
        # Handle case where it's a flat Decimal/float
        if isinstance(vat_data, (Decimal, float, int)):
            return float(taxable_amount) * float(vat_data)
            
        # Handle case where it's a list (brackets)
        if isinstance(vat_data, list) and len(vat_data) > 0:
            rate = getattr(vat_data[0], "rate", 0)
            return float(taxable_amount) * float(rate)
            
        return 0.0

    def validate_income(self, income: float) -> bool:
        """Validate if income is within reasonable bounds"""
        return income >= 0 and income < 1_000_000_000  # < 1 billion

    def validate_deductions(self, deductions: Dict[str, float]) -> bool:
        """Validate deductions don't exceed limits"""
        for category, amount in deductions.items():
            if amount < 0:
                return False
        return True
