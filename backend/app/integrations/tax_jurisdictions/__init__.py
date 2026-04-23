"""
Tax Jurisdictions Package
Provides tax jurisdiction implementations for all supported countries
"""
from .base import BaseTaxJurisdiction, TaxCalculationResult, CapitalGain
from .calculator import TaxCalculator
from .mexico import MexicoTaxJurisdiction
from .brazil import BrazilTaxJurisdiction
from .argentina import ArgentinaTaxJurisdiction
from .colombia import ColombiaTaxJurisdiction
from .peru import PeruTaxJurisdiction
from .chile import ChileTaxJurisdiction


# Map of jurisdiction codes to classes
JURISDICTIONS = {
    "MX": MexicoTaxJurisdiction,
    "BR": BrazilTaxJurisdiction,
    "AR": ArgentinaTaxJurisdiction,
    "CO": ColombiaTaxJurisdiction,
    "PE": PeruTaxJurisdiction,
    "CL": ChileTaxJurisdiction,
}


def get_jurisdiction(code: str) -> BaseTaxJurisdiction:
    """
    Get a tax jurisdiction by code
    
    Args:
        code: Jurisdiction code (MX, BR, AR, CO, PE, CL)
    
    Returns:
        Instantiated tax jurisdiction
    
    Raises:
        ValueError: If jurisdiction code not found
    """
    if code not in JURISDICTIONS:
        raise ValueError(f"Unknown jurisdiction code: {code}. Valid: {list(JURISDICTIONS.keys())}")
    
    jurisdiction_class = JURISDICTIONS[code]
    return jurisdiction_class()


def get_all_jurisdictions() -> dict[str, BaseTaxJurisdiction]:
    """
    Get all available jurisdictions
    
    Returns:
        Dictionary of code -> jurisdiction instance
    """
    return {code: cls() for code, cls in JURISDICTIONS.items()}


__all__ = [
    "BaseTaxJurisdiction",
    "TaxCalculationResult",
    "CapitalGain",
    "TaxCalculator",
    "MexicoTaxJurisdiction",
    "BrazilTaxJurisdiction",
    "ArgentinaTaxJurisdiction",
    "ColombiaTaxJurisdiction",
    "PeruTaxJurisdiction",
    "ChileTaxJurisdiction",
    "JURISDICTIONS",
    "get_jurisdiction",
    "get_all_jurisdictions",
]
