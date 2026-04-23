"""
CSV Exporter
Export tax data to CSV format for spreadsheets
"""
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime
from .base import BaseExporter


class CSVExporter(BaseExporter):
    """
    Export tax data to CSV format
    Suitable for spreadsheets, accounting software, tax authority submission
    """
    
    def generate(self) -> str:
        """Generate CSV export"""
        lines = []
        
        # Header section
        lines.append("# TAX EXPORT - " + self.jurisdiction.name.upper())
        lines.append(f"# Tax Year: {self.tax_year}")
        lines.append(f"# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Taxpayer info
        lines.append("## TAXPAYER INFORMATION")
        lines.append(f"Taxpayer Name,{self.user_tax_profile.tax_payer_name or 'N/A'}")
        lines.append(f"Tax ID ({self.jurisdiction.code}),{self.user_tax_profile.tax_id or 'N/A'}")
        lines.append(f"Tax Address,{self.user_tax_profile.tax_address or 'N/A'}")
        lines.append(f"Tax Advisor,{self.user_tax_profile.tax_advisor_name or 'N/A'}")
        lines.append("")
        
        # Tax summary
        tax_summary = self._get_tax_summary()
        lines.append("## TAX SUMMARY")
        lines.append("Category,Amount,Tax Rate,Tax Amount")
        
        if tax_summary["capital_gains"] > 0:
            rate = (tax_summary["capital_gains_tax"] / tax_summary["capital_gains"] * 100) if tax_summary["capital_gains"] > 0 else Decimal("0")
            lines.append(
                f"Capital Gains,{self._format_decimal(tax_summary['capital_gains'])},{rate:.2f}%,{self._format_decimal(tax_summary['capital_gains_tax'])}"
            )
        
        if tax_summary["ordinary_income"] > 0:
            rate = (tax_summary["ordinary_income_tax"] / tax_summary["ordinary_income"] * 100) if tax_summary["ordinary_income"] > 0 else Decimal("0")
            lines.append(
                f"Ordinary Income,{self._format_decimal(tax_summary['ordinary_income'])},{rate:.2f}%,{self._format_decimal(tax_summary['ordinary_income_tax'])}"
            )
        
        if tax_summary["vat_total"] > 0:
            lines.append(
                f"VAT/IVA,{self._format_decimal(self.tax_calculations.get('vat_base', 0))},{float(self.jurisdiction.vat_rate)*100:.2f}%,{self._format_decimal(tax_summary['vat_total'])}"
            )
        
        lines.append("")
        lines.append("TOTAL TAX LIABILITY,," + f"{float(self.jurisdiction.vat_rate)*100:.2f}%,{self._format_decimal(tax_summary['total_tax'])}")
        lines.append("")
        
        # Transactions detail
        if self.tax_calculations.get("transactions"):
            lines.append("## TRANSACTION DETAIL")
            lines.append("Date,Type,Asset,Quantity,Price,Amount,Fee,Category")
            
            for txn in self.tax_calculations["transactions"]:
                lines.append(
                    f"{txn.get('date', '')},{txn.get('type', '')},{txn.get('asset', '')},{txn.get('quantity', '')},{txn.get('price', '')},{txn.get('amount', '')},{txn.get('fee', '')},{txn.get('tax_category', '')}"
                )
        
        lines.append("")
        lines.append("## NOTES")
        lines.append(f"Filing Authority: {self.jurisdiction.filing_authority}")
        lines.append(f"Filing Deadline: {self._get_filing_deadline()}")
        lines.append(f"Currency: {self.jurisdiction.reporting_currency}")
        
        return "\n".join(lines)
    
    def get_filename(self) -> str:
        """Get CSV filename"""
        tax_id = (self.user_tax_profile.tax_id or "taxpayer").replace(" ", "_")
        return f"tax_export_{self.jurisdiction.code}_{self.tax_year}_{tax_id}.csv"
    
    def get_content_type(self) -> str:
        """Get CSV content type"""
        return "text/csv; charset=utf-8"
