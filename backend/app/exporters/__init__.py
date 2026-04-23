"""
Exporters Package
Tax export functionality for all formats
"""
from .transaction_matcher import TransactionMatcher, MatchedTransaction
from .base import BaseExporter
from .csv_exporter import CSVExporter
from .ods_exporter import ODSExporter
from .pdf_exporter import PDFExporter
from .xml_exporter import XMLExporter


class TaxExportManager:
    """
    Manager for creating tax exports in various formats
    Supports: CSV, ODS, PDF, XML
    """
    
    EXPORTERS = {
        "csv": CSVExporter,
        "ods": ODSExporter,
        "pdf": PDFExporter,
        "xml": XMLExporter,
    }
    
    @classmethod
    def export(
        cls,
        user_tax_profile,
        jurisdiction,
        tax_year: int,
        tax_calculations: dict,
        format: str = "csv"
    ):
        """
        Generate export in specified format
        
        Args:
            user_tax_profile: UserTaxProfile object
            jurisdiction: Jurisdiction object
            tax_year: Tax year (YYYY)
            tax_calculations: Dictionary of tax calculations
            format: Export format ('csv', 'ods', 'pdf', 'xml')
        
        Returns:
            Tuple of (content, filename, content_type)
        """
        format = format.lower()
        
        if format not in cls.EXPORTERS:
            raise ValueError(f"Unknown format: {format}. Supported: {list(cls.EXPORTERS.keys())}")
        
        exporter_class = cls.EXPORTERS[format]
        exporter = exporter_class(user_tax_profile, jurisdiction, tax_year, tax_calculations)
        
        content = exporter.generate()
        filename = exporter.get_filename()
        content_type = exporter.get_content_type()
        
        return content, filename, content_type
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """Get list of supported export formats"""
        return list(cls.EXPORTERS.keys())


__all__ = [
    "TransactionMatcher",
    "MatchedTransaction",
    "BaseExporter",
    "CSVExporter",
    "ODSExporter",
    "PDFExporter",
    "XMLExporter",
    "TaxExportManager",
]
