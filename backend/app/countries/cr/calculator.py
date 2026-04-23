from .config import CostaRica
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Costa Rica-specific tax calculator"""
    
    def __init__(self):
        super().__init__(CostaRica())


__all__ = ["TaxCalculator"]
