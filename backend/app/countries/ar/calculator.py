from datetime import datetime
from .config import Argentina
from ..base.tax_calculator import BaseTaxCalculator
from app.services.financial_data_service import FinancialDataService


class TaxCalculator(BaseTaxCalculator):
    """Argentina-specific tax calculator with CER inflation adjustment"""
    
    def __init__(self):
        super().__init__(Argentina())

    def calculate_inflation_adjusted_gains(
        self, 
        purchase_price: float, 
        sale_price: float, 
        purchase_date: datetime, 
        sale_date: datetime
    ) -> float:
        """
        Calculate capital gains adjusted by CER (inflation index).
        Common in Argentina for tax basis adjustment.
        """
        coef = FinancialDataService.get_inflation_adjustment("AR", purchase_date, sale_date)
        adjusted_basis = purchase_price * float(coef)
        return max(0, sale_price - adjusted_basis)


__all__ = ["TaxCalculator"]
