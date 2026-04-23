"""
ODS (OpenDocument Spreadsheet) Exporter
Export tax data to ODS format for spreadsheets
"""
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
from .base import BaseExporter


class ODSExporter(BaseExporter):
    """
    Export tax data to ODS (OpenDocument Spreadsheet) format
    Requires odfpy library for generation
    Format-compatible with LibreOffice, Excel, Google Sheets
    """
    
    def generate(self) -> bytes:
        """
        Generate ODS export
        
        Note: Requires 'odfpy' package
        For now, returns stub implementation with CSV fallback
        """
        try:
            from odf.opendocument import OpenDocumentSpreadsheet
            from odf.table import Table, TableRow, TableCell
            from odf.text import P
            from odf.style import Style, TextProperties
            
            doc = OpenDocumentSpreadsheet()
            
            # Create summary sheet
            summary_sheet = Table(name="Summary")
            doc.spreadsheet.addElement(summary_sheet)
            
            # Header row
            header_row = TableRow()
            summary_sheet.addElement(header_row)
            
            header_cells = [
                "Category",
                "Amount",
                "Tax Rate",
                "Tax Amount"
            ]
            
            for header in header_cells:
                cell = TableCell(valuetype="string")
                cell.addElement(P(text=header))
                header_row.addElement(cell)
            
            # Summary data
            tax_summary = self._get_tax_summary()
            
            summary_data = [
                ("Taxpayer", self.user_tax_profile.tax_payer_name or "N/A", "", ""),
                ("Tax ID", self.user_tax_profile.tax_id or "N/A", "", ""),
                ("Tax Year", str(self.tax_year), "", ""),
                ("", "", "", ""),
            ]
            
            if tax_summary["capital_gains"] > 0:
                rate = (tax_summary["capital_gains_tax"] / tax_summary["capital_gains"] * 100) if tax_summary["capital_gains"] > 0 else Decimal("0")
                summary_data.append((
                    "Capital Gains",
                    str(tax_summary["capital_gains"]),
                    f"{rate:.2f}%",
                    str(tax_summary["capital_gains_tax"])
                ))
            
            if tax_summary["ordinary_income"] > 0:
                rate = (tax_summary["ordinary_income_tax"] / tax_summary["ordinary_income"] * 100) if tax_summary["ordinary_income"] > 0 else Decimal("0")
                summary_data.append((
                    "Ordinary Income",
                    str(tax_summary["ordinary_income"]),
                    f"{rate:.2f}%",
                    str(tax_summary["ordinary_income_tax"])
                ))
            
            # Add data rows
            for col1, col2, col3, col4 in summary_data:
                row = TableRow()
                summary_sheet.addElement(row)
                
                for value in [col1, col2, col3, col4]:
                    cell = TableCell(valuetype="string")
                    cell.addElement(P(text=str(value)))
                    row.addElement(cell)
            
            # Save to bytes
            from io import BytesIO
            output = BytesIO()
            doc.save(output)
            return output.getvalue()
        
        except ImportError:
            # Fallback: return CSV as bytes if odfpy not available
            csv_content = self._generate_csv_fallback()
            return csv_content.encode('utf-8')
    
    def _generate_csv_fallback(self) -> str:
        """Fallback CSV generation if odfpy not available"""
        lines = []
        
        lines.append("TAX EXPORT - " + self.jurisdiction.name.upper())
        lines.append(f"Tax Year,{self.tax_year}")
        lines.append("")
        
        lines.append("Taxpayer Information")
        lines.append(f"Name,{self.user_tax_profile.tax_payer_name or 'N/A'}")
        lines.append(f"Tax ID,{self.user_tax_profile.tax_id or 'N/A'}")
        lines.append("")
        
        tax_summary = self._get_tax_summary()
        lines.append("Tax Summary")
        lines.append("Category,Amount,Tax Rate,Tax Amount")
        
        if tax_summary["capital_gains"] > 0:
            rate = (tax_summary["capital_gains_tax"] / tax_summary["capital_gains"] * 100) if tax_summary["capital_gains"] > 0 else Decimal("0")
            lines.append(f"Capital Gains,{tax_summary['capital_gains']},{rate:.2f}%,{tax_summary['capital_gains_tax']}")
        
        if tax_summary["ordinary_income"] > 0:
            rate = (tax_summary["ordinary_income_tax"] / tax_summary["ordinary_income"] * 100) if tax_summary["ordinary_income"] > 0 else Decimal("0")
            lines.append(f"Ordinary Income,{tax_summary['ordinary_income']},{rate:.2f}%,{tax_summary['ordinary_income_tax']}")
        
        lines.append(f"TOTAL TAX,,{float(self.jurisdiction.vat_rate)*100:.2f}%,{tax_summary['total_tax']}")
        
        return "\n".join(lines)
    
    def get_filename(self) -> str:
        """Get ODS filename"""
        tax_id = (self.user_tax_profile.tax_id or "taxpayer").replace(" ", "_")
        return f"tax_export_{self.jurisdiction.code}_{self.tax_year}_{tax_id}.ods"
    
    def get_content_type(self) -> str:
        """Get ODS content type"""
        return "application/vnd.oasis.opendocument.spreadsheet"
