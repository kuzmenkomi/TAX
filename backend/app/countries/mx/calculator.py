from datetime import datetime
from .config import Mexico
from ..base.tax_calculator import BaseTaxCalculator
from app.services.financial_data_service import FinancialDataService


class TaxCalculator(BaseTaxCalculator):
    """Mexico-specific tax calculator with UDI inflation adjustment"""
    
    def __init__(self):
        super().__init__(Mexico())
    
    def calculate_isr(self, income: float, deductions: float = 0) -> float:
        """Calculate ISR (Impuesto Sobre la Renta) for Mexico"""
        return self.calculate_income_tax(income, deductions)["income_tax"]

    def calculate_udi_adjusted_cost(
        self, 
        original_cost: float, 
        purchase_date: datetime, 
        sale_date: datetime
    ) -> float:
        """
        Adjust original cost basis using UDI (Unidades de Inversión).
        Standard mechanism for inflation adjustment in Mexico.
        """
        coef = FinancialDataService.get_inflation_adjustment("MX", purchase_date, sale_date)
        return original_cost * float(coef)


__all__ = ["TaxCalculator"]
