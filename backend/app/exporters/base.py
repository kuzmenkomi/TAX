"""
Base Exporter Class
Abstract base for all export formats
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, BinaryIO
from decimal import Decimal
from datetime import datetime
from dataclasses import asdict

from app.models.jurisdiction import Jurisdiction
from app.models.tax_profile import UserTaxProfile


class BaseExporter(ABC):
    """
    Abstract base class for tax export formats
    Subclasses implement specific export formats (PDF, XML, CSV, ODS)
    """
    
    def __init__(
        self,
        user_tax_profile: UserTaxProfile,
        jurisdiction: Jurisdiction,
        tax_year: int,
        tax_calculations: Dict[str, Any]
    ):
        """
        Initialize exporter
        
        Args:
            user_tax_profile: User's tax profile for jurisdiction
            jurisdiction: Jurisdiction object
            tax_year: Tax year for export
            tax_calculations: Dictionary of tax calculations
        """
        self.user_tax_profile = user_tax_profile
        self.jurisdiction = jurisdiction
        self.tax_year = tax_year
        self.tax_calculations = tax_calculations
    
    @abstractmethod
    def generate(self) -> Any:
        """
        Generate export in specific format
        
        Returns:
            Format-specific output (bytes for PDF, string for XML/CSV, etc.)
        """
        pass
    
    @abstractmethod
    def get_filename(self) -> str:
        """
        Get suggested filename for export
        
        Returns:
            Filename with extension
        """
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        """
        Get MIME type for export
        
        Returns:
            Content-Type header value
        """
        pass
    
    # ==================== HELPER METHODS ====================
    
    def _get_header_info(self) -> Dict[str, Any]:
        """Get common header information for all exports"""
        return {
            "tax_year": self.tax_year,
            "jurisdiction_code": self.jurisdiction.code,
            "jurisdiction_name": self.jurisdiction.name,
            "taxpayer_name": self.user_tax_profile.tax_payer_name,
            "tax_id": self.user_tax_profile.tax_id,
            "filing_authority": self.jurisdiction.filing_authority,
            "generated_date": datetime.utcnow().isoformat(),
            "filing_deadline": self._get_filing_deadline(),
            "currency": self.jurisdiction.reporting_currency
        }
    
    def _get_filing_deadline(self) -> str:
        """
        Get filing deadline for jurisdiction
        
        Returns:
            Filing deadline date as string
        """
        from app.integrations.tax_jurisdictions import get_jurisdiction
        
        try:
            jurisdiction = get_jurisdiction(self.jurisdiction.code)
            return jurisdiction.get_filing_deadline(self.tax_year)
        except:
            return "See tax authority website"
    
    def _format_decimal(self, value: Optional[Decimal]) -> str:
        """Format decimal for display"""
        if value is None:
            return "0.00"
        return f"{value:,.2f}"
    
    def _format_date(self, date: datetime) -> str:
        """Format date for display"""
        return date.strftime("%Y-%m-%d")
    
    def _get_tax_summary(self) -> Dict[str, Decimal]:
        """Extract tax summary from calculations"""
        summary = {
            "capital_gains": Decimal("0"),
            "capital_gains_tax": Decimal("0"),
            "ordinary_income": Decimal("0"),
            "ordinary_income_tax": Decimal("0"),
            "vat_total": Decimal("0"),
            "total_tax": Decimal("0")
        }
        
        for calc_key, calc_value in self.tax_calculations.items():
            if calc_key == "capital_gains":
                summary["capital_gains"] = Decimal(str(calc_value.get("amount", 0)))
                summary["capital_gains_tax"] = Decimal(str(calc_value.get("tax", 0)))
            elif calc_key == "ordinary_income":
                summary["ordinary_income"] = Decimal(str(calc_value.get("amount", 0)))
                summary["ordinary_income_tax"] = Decimal(str(calc_value.get("tax", 0)))
            elif calc_key == "vat":
                summary["vat_total"] = Decimal(str(calc_value.get("tax", 0)))
        
        summary["total_tax"] = (
            summary["capital_gains_tax"] +
            summary["ordinary_income_tax"] +
            summary["vat_total"]
        )
        
        return summary
