# Countries module - central hub for all LatAm countries
# Provides plugin-based architecture for multi-country support

from app.countries.base import (
    BaseCountryDefinition,
    CentralAmericaBase,
    SouthAmericaBase,
    NorthAmericaBase,
    BaseTaxCalculator,
    TaxType,
    TaxBracket,
    DeductionRule,
    TaxForm,
    SubmissionResult,
    ComplianceCheckResult,
)

from app.countries.registries import CountryRegistry

__all__ = [
    # Base classes
    "BaseCountryDefinition",
    "CentralAmericaBase",
    "SouthAmericaBase",
    "NorthAmericaBase",
    "BaseTaxCalculator",
    # Enums and data classes
    "TaxType",
    "TaxBracket",
    "DeductionRule",
    "TaxForm",
    "SubmissionResult",
    "ComplianceCheckResult",
    # Registry
    "CountryRegistry",
]

# Import and auto-register all 11 countries
# This ensures all countries are available when this module is imported

# ============== 6 EXISTING COUNTRIES (Refactored) ==============
from app.countries.mx.config import Mexico
from app.countries.br.config import Brazil
from app.countries.ar.config import Argentina
from app.countries.co.config import Colombia
from app.countries.pe.config import Peru
from app.countries.cl.config import Chile

# ============== 1 COUNTRY FROM WEEK 1 ==============
from app.countries.gt.config import Guatemala

# ============== 4 NEW COUNTRIES (WEEK 3+) ==============
from app.countries.ec.config import Ecuador
from app.countries.uy.config import Uruguay
from app.countries.cr.config import CostaRica
from app.countries.hn.config import Honduras
from app.countries.bo.config import Bolivia
from app.countries.us.config import UnitedStates

# ============== AUTO-REGISTER ALL COUNTRIES ==============
# Plugin pattern: no if/elif chains, pure registry
CountryRegistry.register(Mexico)
CountryRegistry.register(Brazil)
CountryRegistry.register(Argentina)
CountryRegistry.register(Colombia)
CountryRegistry.register(Peru)
CountryRegistry.register(Chile)
CountryRegistry.register(Guatemala)
CountryRegistry.register(Ecuador)
CountryRegistry.register(Uruguay)
CountryRegistry.register(CostaRica)
CountryRegistry.register(Honduras)
CountryRegistry.register(Bolivia)
CountryRegistry.register(UnitedStates)
# from app.countries.cr.config import CostaRica
# from app.countries.hn.config import Honduras
# CountryRegistry.register(Ecuador)
# CountryRegistry.register(Uruguay)
# CountryRegistry.register(CostaRica)
# CountryRegistry.register(Honduras)
