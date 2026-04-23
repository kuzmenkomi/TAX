# Base module initialization
# Exports all base classes for easy importing

from .definitions import (
    BaseCountryDefinition,
    BaseTaxAuthorityClient,
    CentralAmericaBase,
    SouthAmericaBase,
    NorthAmericaBase,
    TaxType,
    TaxBracket,
    DeductionRule,
    TaxForm,
    SubmissionResult,
    ComplianceCheckResult,
    SubmissionStatus,
    ComplianceStatus,
)

from .tax_calculator import BaseTaxCalculator

__all__ = [
    "BaseCountryDefinition",
    "BaseTaxAuthorityClient",
    "CentralAmericaBase",
    "SouthAmericaBase",
    "NorthAmericaBase",
    "BaseTaxCalculator",
    "TaxType",
    "TaxBracket",
    "DeductionRule",
    "TaxForm",
    "SubmissionResult",
    "ComplianceCheckResult",
    "SubmissionStatus",
    "ComplianceStatus",
]
