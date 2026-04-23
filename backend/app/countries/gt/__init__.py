# Guatemala country module initialization
# Provides unified access to all Guatemala tax functionality

from .config import Guatemala
from .calculator import TaxCalculator

__all__ = [
    "Guatemala",
    "TaxCalculator",
]
