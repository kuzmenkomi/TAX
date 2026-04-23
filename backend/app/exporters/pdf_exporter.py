"""
PDF Exporter
Export tax forms to PDF format for printing and filing
"""
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
from .base import BaseExporter


class PDFExporter(BaseExporter):
    """
    Export tax forms to PDF format
    Jurisdiction-specific form layouts
    
    Requires reportlab library for PDF generation
    """
    
    def generate(self) -> bytes:
        """
        Generate PDF export
        Returns bytes for file download
        
        Note: Requires 'reportlab' package
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=HexColor('#1f4788'),
                spaceAfter=12
            )
            
            # Title
            title = f"TAX DECLARATION - {self.jurisdiction.name.upper()}"
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Taxpayer info
            elements.append(Paragraph("TAXPAYER INFORMATION", styles['Heading3']))
            taxpayer_data = [
                ["Field", "Value"],
                ["Name", self.user_tax_profile.tax_payer_name or "N/A"],
                ["Tax ID", self.user_tax_profile.tax_id or "N/A"],
                ["Address", self.user_tax_profile.tax_address or "N/A"],
                ["Tax Year", str(self.tax_year)],
            ]
            
            tax_table = Table(taxpayer_data, colWidths=[2*inch, 4*inch])
            tax_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#cccccc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#000000')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#000000')),
            ]))
            
            elements.append(tax_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Tax summary
            elements.append(Paragraph("TAX CALCULATION SUMMARY", styles['Heading3']))
            
            tax_summary = self._get_tax_summary()
            summary_data = [["Category", "Amount", "Tax Rate", "Tax"]]
            
            if tax_summary["capital_gains"] > 0:
                rate = (tax_summary["capital_gains_tax"] / tax_summary["capital_gains"] * 100) if tax_summary["capital_gains"] > 0 else Decimal("0")
                summary_data.append([
                    "Capital Gains",
                    self._format_decimal(tax_summary["capital_gains"]),
                    f"{rate:.2f}%",
                    self._format_decimal(tax_summary["capital_gains_tax"])
                ])
            
            if tax_summary["ordinary_income"] > 0:
                rate = (tax_summary["ordinary_income_tax"] / tax_summary["ordinary_income"] * 100) if tax_summary["ordinary_income"] > 0 else Decimal("0")
                summary_data.append([
                    "Ordinary Income",
                    self._format_decimal(tax_summary["ordinary_income"]),
                    f"{rate:.2f}%",
                    self._format_decimal(tax_summary["ordinary_income_tax"])
                ])
            
            summary_data.append([
                "TOTAL TAX",
                "",
                "",
                self._format_decimal(tax_summary["total_tax"])
            ])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#ffffcc')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#000000')),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Footer
            elements.append(Spacer(1, 0.2*inch))
            footer_text = f"Filing Authority: {self.jurisdiction.filing_authority} | Deadline: {self._get_filing_deadline()} | Currency: {self.jurisdiction.reporting_currency}"
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=HexColor('#666666')
            )))
            
            # Build PDF
            doc.build(elements)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
        
        except ImportError:
            # Fallback: return text as bytes if reportlab not available
            text = f"TAX DECLARATION - {self.jurisdiction.name}\n"
            text += f"Tax Year: {self.tax_year}\n"
            text += f"Taxpayer: {self.user_tax_profile.tax_payer_name}\n"
            text += f"Tax ID: {self.user_tax_profile.tax_id}\n\n"
            
            tax_summary = self._get_tax_summary()
            text += "TAX SUMMARY:\n"
            text += f"Capital Gains Tax: {self._format_decimal(tax_summary['capital_gains_tax'])}\n"
            text += f"Income Tax: {self._format_decimal(tax_summary['ordinary_income_tax'])}\n"
            text += f"Total Tax: {self._format_decimal(tax_summary['total_tax'])}\n"
            
            return text.encode('utf-8')
    
    def get_filename(self) -> str:
        """Get PDF filename"""
        tax_id = (self.user_tax_profile.tax_id or "taxpayer").replace(" ", "_")
        return f"tax_declaration_{self.jurisdiction.code}_{self.tax_year}_{tax_id}.pdf"
    
    def get_content_type(self) -> str:
        """Get PDF content type"""
        return "application/pdf"
