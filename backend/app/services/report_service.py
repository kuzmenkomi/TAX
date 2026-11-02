import io
import logging
from datetime import datetime
from typing import Any
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

class ReportService:
    """
    Service for generating official tax reports in PDF and XML formats.
    """
    
    @staticmethod
    def generate_pdf_report(user, jurisdiction_code, year, data: dict[str, Any]):
        """
        Generates a professional PDF tax report using real analysis data.
        """
        try:
            pnl = data.get("pnl", {})
            realized_pnl = pnl.get("realized_pnl_by_asset", {})
            lot_matches = pnl.get("lot_matches", [])
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            def draw_page_footer(canvas_obj):
                canvas_obj.saveState()
                canvas_obj.setFillColor(colors.HexColor("#64748B"))
                canvas_obj.setFont("Helvetica", 7)
                canvas_obj.drawString(50, 30, "Disclaimer: This report is for informational purposes only. Please see full legal disclaimer on the last page.")
                canvas_obj.restoreState()
            
            # --- Header ---
            p.setFillColor(colors.HexColor("#0F172A")) # Slate 900
            p.rect(0, height - 120, width, 120, fill=1, stroke=0)
            
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 26)
            p.drawString(50, height - 60, "TAXFLOW OFFICIAL REPORT")
            
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 85, f"CRYPTO ASSET TAX COMPLIANCE · {jurisdiction_code.upper()} · {year}")
            p.drawRightString(width - 50, height - 85, "CONFIDENTIAL DOCUMENT")

            # --- User Info ---
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 11)
            p.drawString(50, height - 160, "TAXPAYER PROFILE")
            
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 180, f"Email: {user.email}")
            p.drawString(50, height - 195, f"Jurisdiction: {jurisdiction_code.upper()}")
            p.drawString(50, height - 210, f"Generated On: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
            
            # --- Summary Cards ---
            p.line(50, height - 230, width - 50, height - 230)
            
            # Draw Summary Boxes
            total_gain = sum(v for v in realized_pnl.values() if v > 0)
            total_loss = sum(v for v in realized_pnl.values() if v < 0)
            net_pnl = sum(realized_pnl.values())
            
            def draw_stat_box(x, y, label, value, color):
                p.setFillColor(colors.HexColor("#F8FAFC"))
                p.roundRect(x, y, 160, 60, 8, fill=1, stroke=0)
                p.setFillColor(colors.HexColor("#64748B"))
                p.setFont("Helvetica-Bold", 8)
                p.drawString(x + 15, y + 40, label.upper())
                p.setFillColor(color)
                p.setFont("Helvetica-Bold", 14)
                p.drawString(x + 15, y + 15, f"${value:,.2f}")

            draw_stat_box(50, height - 310, "Total Realized Gains", total_gain, colors.HexColor("#10B981"))
            draw_stat_box(225, height - 310, "Total Realized Losses", total_loss, colors.HexColor("#EF4444"))
            draw_stat_box(400, height - 310, "Net Capital Gain/Loss", net_pnl, colors.black)

            # --- Asset Breakdown ---
            y = height - 360
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, "ASSET BREAKDOWN")
            
            y -= 25
            p.setFont("Helvetica-Bold", 9)
            p.setFillColor(colors.HexColor("#E2E8F0"))
            p.rect(50, y - 5, width - 100, 18, fill=1, stroke=0)
            p.setFillColor(colors.black)
            p.drawString(60, y, "ASSET")
            p.drawString(200, y, "REALIZED GAIN/LOSS (USD)")
            p.drawString(400, y, "TAXABLE EVENTS")
            
            y -= 20
            p.setFont("Helvetica", 9)
            for asset, gain in sorted(realized_pnl.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
                if y < 100: # New page if needed
                    draw_page_footer(p)
                    p.showPage()
                    y = height - 50
                p.drawString(60, y, asset)
                p.setFillColor(colors.HexColor("#10B981") if gain >= 0 else colors.HexColor("#EF4444"))
                p.drawString(200, y, f"${gain:,.2f}")
                p.setFillColor(colors.black)
                p.drawString(400, y, str(len([m for m in lot_matches if m['asset'] == asset])))
                y -= 18

            # --- Footer ---
            draw_page_footer(p)
            p.showPage()

            # --- Legal Disclaimer Page ---
            p.setFillColor(colors.HexColor("#0F172A")) # Slate 900
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, height - 80, "Legal Disclaimer")
            
            p.setStrokeColor(colors.HexColor("#E2E8F0"))
            p.setLineWidth(0.5)
            p.line(50, height - 95, width - 50, height - 95)
            
            disclaimer_style = ParagraphStyle(
                "DisclaimerText",
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=colors.HexColor("#475569")
            )
            
            disclaimer_text = [
                "This tax report is generated automatically by Declairo based on transaction data provided by the user. Declairo is a software tool and does not provide tax, legal, or financial advice.",
                "Cryptocurrency tax regulations vary by jurisdiction and may change over time. The accuracy and completeness of this report depend on the accuracy of the imported transaction data and selected calculation settings.",
                "Users are responsible for reviewing all calculations and are strongly encouraged to consult a qualified tax professional before filing any tax documents.",
                "Declairo assumes no responsibility or liability for any errors, omissions, tax obligations, penalties, or losses resulting from the use of this report or software."
            ]
            
            y_pos = height - 110
            for paragraph in disclaimer_text:
                p_obj = Paragraph(paragraph, disclaimer_style)
                w, h = p_obj.wrap(width - 100, height)
                y_pos -= h
                p_obj.drawOn(p, 50, y_pos)
                y_pos -= 10
                
            draw_page_footer(p)
            p.showPage()
            p.save()

            buffer.seek(0)
            filename = f"TaxFlow_Report_{jurisdiction_code.upper()}_{year}.pdf"
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as e:
            logger.error(f"PDF Generation Error: {str(e)}")
            raise

    @staticmethod
    def generate_turbotax_csv(data: dict[str, Any]):
        """
        Generates a CSV for TurboTax/TaxAct.
        """
        from app.exporters.turbotax_exporter import export_turbotax_csv
        lot_matches = data.get("pnl", {}).get("lot_matches", [])
        buffer = export_turbotax_csv(lot_matches)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=turbotax_export.csv"}
        )

    @staticmethod
    def generate_xml_report(user, jurisdiction_code, year, data):
        """
        Generates a basic XML tax report (Legacy compatibility).
        """
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<TaxReport>
    <Header>
        <Version>1.0</Version>
        <Jurisdiction>{jurisdiction_code}</Jurisdiction>
        <Year>{year}</Year>
        <Taxpayer>{user.email}</Taxpayer>
    </Header>
    <Summary>
        <GeneratedOn>{datetime.utcnow().isoformat()}</GeneratedOn>
    </Summary>
</TaxReport>
"""
        return StreamingResponse(
            io.BytesIO(xml_content.encode('utf-8')),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=tax_report_{jurisdiction_code}_{year}.xml"}
        )

    @staticmethod
    def generate_latam_export(jurisdiction_code: str, data: dict[str, Any]):
        """
        Generates a localized report for Latin American countries.
        """
        from app.exporters import latam_exporters
        lot_matches = data.get("pnl", {}).get("lot_matches", [])
        
        j_code = jurisdiction_code.lower()
        if j_code == "ar": # Argentina
            buffer = latam_exporters.export_afip_csv(lot_matches)
            filename = f"afip_export_{datetime.now().strftime('%Y%m%d')}.csv"
            media_type = "text/csv"
        elif j_code == "mx": # Mexico
            buffer = latam_exporters.export_sat_mexico_json(lot_matches)
            filename = f"sat_mexico_export_{datetime.now().strftime('%Y%m%d')}.json"
            media_type = "application/json"
        elif j_code == "cl": # Chile
            buffer = latam_exporters.export_sii_chile_csv(lot_matches)
            filename = f"sii_chile_export_{datetime.now().strftime('%Y%m%d')}.csv"
            media_type = "text/csv"
        elif j_code == "co": # Colombia
            buffer = latam_exporters.export_dian_colombia_csv(lot_matches)
            filename = f"dian_colombia_export_{datetime.now().strftime('%Y%m%d')}.csv"
            media_type = "text/csv"
        else:
            raise ValueError(f"Jurisdiction {jurisdiction_code} not supported for specialized LatAm export")

        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
