# Base Country Definition for all LatAm countries
# This is the foundational class that all countries must implement

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


class TaxType(Enum):
    """Type of tax supported by the system"""
    INCOME_TAX = "income_tax"
    CAPITAL_GAINS = "capital_gains"
    DIVIDEND_TAX = "dividend_tax"
    VAT = "vat"
    WEALTH_TAX = "wealth_tax"
    CRYPTO_TAX = "crypto_tax"
    DEFI_TAX = "defi_tax"


class SubmissionStatus(Enum):
    """Status of tax filing submission"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AMENDED = "amended"
    PROCESSING = "processing"
    ERROR = "error"


class ComplianceStatus(Enum):
    """Status of compliance check"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"


@dataclass
class TaxBracket:
    """Single tax bracket for progressive taxation"""
    min_amount: float
    max_amount: float
    rate: float
    notes: str = ""

    def applies_to(self, amount: float) -> bool:
        """Check if this bracket applies to given amount"""
        return self.min_amount <= amount < self.max_amount


@dataclass
class DeductionRule:
    """One deduction rule for tax purposes"""
    category: str                  # "housing", "education", "health", etc.
    rate: Optional[float] = None   # % of income (if applicable)
    max_amount: float = float('inf')  # Absolute maximum
    min_income: float = 0          # Minimum income threshold
    description: str = ""          # Human readable (optional)
    conditions: List[str] = field(default_factory=list)  # Additional conditions
    is_percentage: bool = True     # Is it % of income or absolute amount?

    def calculate(self, income: float, base_amount: float = 0) -> float:
        """Calculate deduction amount"""
        try:
            dec_income = Decimal(str(income))
        except (TypeError, ValueError):
            return 0.0

        if dec_income < Decimal(str(self.min_income)):
            return 0.0
        
        if self.is_percentage:
            deduction = dec_income * Decimal(str(self.rate or 0))
        else:
            deduction = Decimal(str(base_amount))
        
        return float(min(deduction, Decimal(str(self.max_amount))))


@dataclass
class TaxForm:
    """Definition of a required tax form"""
    code: str                      # Form code (e.g., "IRPF", "F-101")
    name: str                      # Form name
    deadline: str                  # Deadline (e.g., "2024-04-30")
    required: bool                 # Is it always required?
    conditions: Optional[List[str]] = None  # When is it required?
    url: Optional[str] = None      # Link to form
    fields: List[str] = field(default_factory=list)  # Required fields


@dataclass
class SubmissionResult:
    """Result of submitting a tax filing"""
    status: SubmissionStatus
    submission_id: str
    timestamp: datetime
    message: str
    receipt_number: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceCheckResult:
    """Result of compliance validation"""
    status: ComplianceStatus
    is_valid: bool
    checks_performed: List[str]
    issues: List[str]
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class BaseCountryDefinition(ABC):
    """
    Abstract base class that defines the interface for all countries.
    
    Each country implementation must provide:
    - Tax rates and brackets
    - Deduction rules
    - Tax forms
    - Taxpayer ID validation
    - Currency formatting
    """

    # Required class attributes - must be overridden in subclass
    country_code: str              # ISO 2-letter code: "GT", "EC", "UY", etc.
    country_name: str              # Full name: "Guatemala", "Ecuador", etc.
    country_region: str            # Region: "Central America", "South America"
    currency: str                  # Currency code: "GTQ", "USD", "UYU", etc.
    currency_symbol: str           # Symbol: "Q", "$", "$U", etc.
    tax_authority: str             # Authority name: "SAT", "SRI", "DGI", etc.
    tax_authority_url: str = ""    # Official website
    tax_year: int = 2025           # Current tax year (e.g., 2025)
    filing_deadline_month_day: str = "04-30" # Format: "MM-DD"
    filing_deadline_full: str = "2026-04-30"      # Format: "YYYY-MM-DD"
    
    # API configuration
    has_api: bool = False          # Has official tax authority API?
    api_base_url: Optional[str] = None
    api_documentation_url: Optional[str] = None
    
    # Taxpayer ID format
    taxpayer_id_format: str        # "NIT (11 digits)", "RFC (16 chars)", etc.
    taxpayer_id_regex: str         # Regex validation pattern
    taxpayer_id_length: int        # Expected length

    @abstractmethod
    def get_tax_rates(self) -> Dict[TaxType, List[TaxBracket]]:
        """
        Return all applicable tax rates for this country.
        
        Returns:
            Dictionary mapping tax types to lists of brackets
            
        Example:
        {
            TaxType.INCOME_TAX: [
                TaxBracket(0, 5000, 0.05),
                TaxBracket(5000, 20000, 0.07),
                TaxBracket(20000, float('inf'), 0.31),
            ],
            TaxType.CAPITAL_GAINS: [
                TaxBracket(0, float('inf'), 0.31),
            ],
        }
        """
        pass

    @abstractmethod
    def get_deductions(self) -> Dict[str, DeductionRule]:
        """
        Return all available deduction rules for this country.
        
        Returns:
            Dictionary mapping deduction categories to rules
        """
        pass

    @abstractmethod
    def get_tax_forms(self) -> Dict[str, TaxForm]:
        """
        Return all required tax forms for this country and year.
        
        Returns:
            Dictionary mapping form codes to form definitions
        """
        pass

    @abstractmethod
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """
        Validate if a taxpayer ID is correctly formatted.
        Should check format, length, and any check digits.
        
        Args:
            taxpayer_id: The ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def format_currency(self, amount: float, symbol: bool = True) -> str:
        """
        Format an amount in the country's currency.
        
        Args:
            amount: Amount to format
            symbol: Include currency symbol?
            
        Returns:
            Formatted string like "Q 1,234.56" or "1,234.56 GTQ"
        """
        pass

    # Optional methods with default implementations

    def get_country_info(self) -> Dict[str, Any]:
        """Get comprehensive country information"""
        return {
            "code": self.country_code,
            "name": self.country_name,
            "region": self.country_region,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority,
            "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full,
            "has_api": self.has_api,
            "api_base_url": self.api_base_url,
            "taxpayer_id_format": self.taxpayer_id_format,
        }

    def calculate_progressive_tax(
        self,
        amount: float,
        tax_type: TaxType,
    ) -> Dict[str, Any]:
        """
        Calculate progressive tax for given amount and type.
        
        Args:
            amount: Base amount to tax
            tax_type: Type of tax
            
        Returns:
            Dictionary with breakdown:
            {
                "gross_tax": 1000,
                "effective_rate": 0.15,
                "brackets": [
                    {"min": 0, "max": 5000, "rate": 0.05, "tax": 250},
                    ...
                ]
            }
        """
        from decimal import Decimal
        
        rates = self.get_tax_rates().get(tax_type, [])
        if not rates:
            return {"gross_tax": 0.0, "effective_rate": 0.0, "brackets": []}

        # Convert everything to Decimal to prevent floating point errors
        try:
            dec_amount = Decimal(str(amount))
        except (TypeError, ValueError):
            dec_amount = Decimal(0)
            
        total_tax = Decimal(0)
        brackets_breakdown = []

        for bracket in sorted(rates, key=lambda b: float(b.min_amount)):
            dec_min = Decimal(str(bracket.min_amount))
            if dec_amount <= dec_min:
                break

            dec_max = Decimal(str(bracket.max_amount))
            taxable_at_bracket = min(dec_amount, dec_max) - dec_min
            
            dec_rate = Decimal(str(bracket.rate))
            tax_at_bracket = taxable_at_bracket * dec_rate

            total_tax += tax_at_bracket
            brackets_breakdown.append({
                "min": float(dec_min),
                "max": float(dec_max),
                "rate": float(dec_rate),
                "tax": float(tax_at_bracket),
            })

        gross_tax = float(total_tax)
        effective_rate = float(total_tax / dec_amount) if dec_amount > 0 else 0.0

        return {
            "gross_tax": gross_tax,
            "effective_rate": effective_rate,
            "brackets": brackets_breakdown,
        }

    def get_applicable_deductions(self, income: float) -> Dict[str, float]:
        """
        Get applicable deductions for given income level.
        
        Args:
            income: Taxpayer income
            
        Returns:
            Dictionary of applicable deductions and amounts
        """
        deductions = self.get_deductions()
        applicable = {}

        for name, rule in deductions.items():
            if income >= rule.min_income:
                amount = rule.calculate(income)
                if amount > 0:
                    applicable[name] = amount

        return applicable


# For future use - template for common regional patterns
class NorthAmericaBase(BaseCountryDefinition):
    """Base class for North American countries with common patterns"""
    country_region = "North America"
    pass


class CentralAmericaBase(BaseCountryDefinition):
    """Base class for Central American countries with common patterns"""
    country_region = "Central America"
    pass


class SouthAmericaBase(BaseCountryDefinition):
    """Base class for South American countries with common patterns"""
    country_region = "South America"
    pass


# ============== TAX AUTHORITY API BASE CLASS ==============

class BaseTaxAuthorityClient(ABC):
    """
    Abstract base class for tax authority API clients.
    Each country can implement its own tax authority client for filing,
    verification, and compliance checking.
    """
    
    country_code: str
    tax_authority: str
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with tax authority"""
        pass
    
    @abstractmethod
    def submit_filing(self, data: Dict[str, Any]) -> SubmissionResult:
        """Submit tax filing to authority"""
        pass
    
    @abstractmethod
    def get_filing_status(self, filing_id: str) -> Dict[str, Any]:
        """Get status of submitted filing"""
        pass
    
    @abstractmethod
    def check_compliance(self, data: Dict[str, Any]) -> ComplianceCheckResult:
        """Check if data meets compliance requirements"""
        pass
    
    @abstractmethod
    def get_filing_forms(self) -> Dict[str, TaxForm]:
        """Get available forms for this tax authority"""
        pass

