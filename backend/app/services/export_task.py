import os
import io
import csv
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List
import pandas as pd

from sqlalchemy.orm import Session
from app.models import AnalysisRun, User
from app.models.jurisdiction import Jurisdiction
from app.models.tax_profile import UserTaxProfile

logger = logging.getLogger(__name__)

def generate_csv_export(run: AnalysisRun, db: Session) -> str:
    """
    Builds RFC 4180 CSV from AnalysisRun transaction data.
    Columns: Date, Type, Asset, Quantity, Price (USD), Realized P&L, Fee, Category
    """
    from app.routers.v1.exports import _get_csv_path, _get_summary
    
    csv_path = _get_csv_path(run)
    df = pd.read_csv(csv_path)
    
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    
    # Header per RFC 4180
    writer.writerow(["Date", "Type", "Asset", "Quantity", "Price (USD)", "Realized P&L", "Fee", "Category"])
    
    summary = _get_summary(run)
    pnl = summary.get("pnl", {})
    lot_matches = pnl.get("lot_matches", [])
    
    # Create lookup map for lot matches by sell transaction ID
    match_lookup = {}
    for match in lot_matches:
        sell_id = match.get("sell_tx_id")
        sell_ext_id = match.get("sell_tx_external_id")
        key = str(sell_id) if sell_id is not None else str(sell_ext_id)
        if key:
            if key not in match_lookup:
                match_lookup[key] = 0.0
            match_lookup[key] += float(match.get("gain_loss", 0.0))
            
    for _, row in df.iterrows():
        # Date & timestamps
        date_str = str(row.get("timestamp", ""))
        tx_type = str(row.get("type", row.get("tx_type", "")))
        asset = str(row.get("asset", ""))
        qty = float(row.get("amount", 0.0))
        price = float(row.get("price", 0.0))
        fee = float(row.get("fee", 0.0))
        category = str(row.get("custom_tag", "")) if row.get("custom_tag") and str(row.get("custom_tag")) != "nan" else ""
        
        # Determine P&L
        row_id = row.get("id")
        row_ext_id = row.get("external_id")
        
        realized_pnl = 0.0
        if tx_type.upper() in ("SELL", "SWAP", "LIQUIDATION"):
            lookup_key = str(row_id) if row_id is not None else str(row_ext_id)
            realized_pnl = match_lookup.get(lookup_key, 0.0)
            
        writer.writerow([
            date_str,
            tx_type,
            asset,
            f"{qty:.8f}".rstrip('0').rstrip('.'),
            f"{price:.2f}",
            f"{realized_pnl:.2f}",
            f"{fee:.8f}".rstrip('0').rstrip('.'),
            category
        ])
        
    return output.getvalue()


def generate_pdf_export(run: AnalysisRun, db: Session, user: User) -> bytes:
    """
    Builds a professional Declairo PDF report using ReportLab.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.pdfgen import canvas
    
    from app.routers.v1.exports import _get_summary
    
    summary = _get_summary(run)
    pnl = summary.get("pnl", {})
    realized_pnl_by_asset = pnl.get("realized_pnl_by_asset", {})
    lot_matches = pnl.get("lot_matches", [])
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Canvas wrapper
    class WrappedNumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            self._saved_page_states = []
            super().__init__(*args, **kwargs)
            
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                super().showPage()
            super().save()

        def draw_page_number(self, page_count):
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(self._pagesize[0] - 54, 36, page_text)
            
            # Disclaimer footer in 7pt
            self.setFont("Helvetica", 7)
            self.drawString(54, 36, "Disclaimer: This report is for informational purposes only. Please see full legal disclaimer on the last page.")
            
            if self._pageNumber > 1:
                self.setFont("Helvetica", 8)
                self.setStrokeColor(HexColor("#E2E8F0"))
                self.setLineWidth(0.5)
                self.line(54, self._pagesize[1] - 54, self._pagesize[0] - 54, self._pagesize[1] - 54)
                self.drawString(54, self._pagesize[1] - 46, "Declairo Tax Compliance Report")
                self.drawRightString(self._pagesize[0] - 54, self._pagesize[1] - 46, datetime.now().strftime("%Y-%m-%d"))
            self.restoreState()
            
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Brand Typography & Colors
    # Declairo palette: #0b0f15 (Dark Header), #00e5a0 (Green Accent), #00ba88 (Success State), #f8fafc (Subtle BG)
    title_style = ParagraphStyle(
        'CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=32,
        textColor=HexColor('#0b0f15'),
        leading=38,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        fontName='Helvetica',
        fontSize=12,
        textColor=HexColor('#64748B'),
        leading=16,
        spaceAfter=40
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=HexColor('#0b0f15'),
        spaceBefore=15,
        spaceAfter=15,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        fontName='Helvetica',
        fontSize=10,
        textColor=HexColor('#1E293B'),
        leading=14
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=HexColor('#FFFFFF'),
        leading=12
    )
    
    table_body_style = ParagraphStyle(
        'TableBody',
        fontName='Helvetica',
        fontSize=9,
        textColor=HexColor('#1E293B'),
        leading=12
    )

    table_body_bold_style = ParagraphStyle(
        'TableBodyBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=HexColor('#1E293B'),
        leading=12
    )
    
    # ============================================================
    # PAGE 1: COVER PAGE
    # ============================================================
    
    # Logo embedding if available
    logo_path = "logo_site.png"
    if os.path.exists(logo_path):
        try:
            # Create a compact header logo
            logo_img = Image(logo_path, width=150, height=45)
            logo_img.hAlign = 'LEFT'
            elements.append(logo_img)
            elements.append(Spacer(1, 0.4 * inch))
        except Exception as e:
            logger.warning(f"Could not load PDF logo: {e}")
            elements.append(Spacer(1, 0.6 * inch))
    else:
        elements.append(Spacer(1, 0.6 * inch))
        
    elements.append(Paragraph("Official Tax Report", title_style))
    elements.append(Paragraph(f"Crypto Asset Tax Compliance · FIFO Method", subtitle_style))
    
    # Colored banner bar (Green Accent)
    banner_data = [[""]]
    banner_table = Table(banner_data, colWidths=[doc.width])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#00e5a0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 0.4 * inch))
    
    # Profile Card info
    tax_payer_name = user.full_name or user.email
    jurisdiction_code = user.jurisdiction_code or "BR"
    
    profile_data = [
        [Paragraph("<b>TAXPAYER PROFILE</b>", table_body_bold_style), ""],
        [Paragraph("Taxpayer Name", table_body_style), Paragraph(tax_payer_name, table_body_style)],
        [Paragraph("Email Address", table_body_style), Paragraph(user.email, table_body_style)],
        [Paragraph("Jurisdiction", table_body_style), Paragraph(jurisdiction_code.upper(), table_body_style)],
        [Paragraph("Reporting Period", table_body_style), Paragraph(f"Fiscal Year {datetime.now().year - 1}", table_body_style)],
        [Paragraph("Filing Method", table_body_style), Paragraph("FIFO (First In, First Out)", table_body_style)],
        [Paragraph("Generated On", table_body_style), Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), table_body_style)]
    ]
    
    profile_table = Table(profile_data, colWidths=[2.5*inch, 3.5*inch])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#F8FAFC')),
        ('SPAN', (0,0), (1,0)),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(profile_table)
    
    elements.append(PageBreak())
    
    # ============================================================
    # PAGE 2: SUMMARY TABLE & METRICS
    # ============================================================
    elements.append(Paragraph("Tax Calculation Summary", section_heading))
    
    total_gain = float(sum(v for v in realized_pnl_by_asset.values() if v > 0))
    total_loss = float(sum(v for v in realized_pnl_by_asset.values() if v < 0))
    net_pnl = float(sum(realized_pnl_by_asset.values()))
    
    # 3 Summary metrics cards
    metrics_data = [
        [
            Paragraph("<font size=10 color='#64748B'><b>TOTAL REALIZED GAINS</b></font><br/><br/><font size=14 color='#00ba88'><b>$" + f"{total_gain:,.2f}" + "</b></font>", body_style),
            Paragraph("<font size=10 color='#64748B'><b>TOTAL REALIZED LOSSES</b></font><br/><br/><font size=14 color='#EF4444'><b>$" + f"{total_loss:,.2f}" + "</b></font>", body_style),
            Paragraph("<font size=10 color='#64748B'><b>NET CAPITAL GAIN/LOSS</b></font><br/><br/><font size=14 color='#0b0f15'><b>$" + f"{net_pnl:,.2f}" + "</b></font>", body_style),
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Asset Breakdown Table
    elements.append(Paragraph("Asset Capital Gains Breakdown", section_heading))
    breakdown_data = [[
        Paragraph("Asset", table_header_style),
        Paragraph("Realized Gain / Loss (USD)", table_header_style),
        Paragraph("Taxable Events", table_header_style)
    ]]
    
    for asset, gain in sorted(realized_pnl_by_asset.items(), key=lambda x: abs(x[1]), reverse=True):
        if asset == "GAS_EXPENSE":
            continue
        events_count = len([m for m in lot_matches if m.get('asset') == asset])
        breakdown_data.append([
            Paragraph(asset, table_body_bold_style),
            Paragraph(f"${gain:,.2f}", table_body_bold_style if gain >= 0 else ParagraphStyle('RedText', parent=table_body_bold_style, textColor=HexColor('#EF4444'))),
            Paragraph(str(events_count), table_body_style)
        ])
        
    breakdown_table = Table(breakdown_data, colWidths=[2.0*inch, 2.5*inch, 1.5*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#0b0f15')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(breakdown_table)
    
    elements.append(PageBreak())
    
    # ============================================================
    # PAGE 3+: LOT-MATCH DETAILS
    # ============================================================
    elements.append(Paragraph("Detailed Capital Gain Transactions", section_heading))
    
    # We wrap cells to prevent overflow
    matches_header = [
        Paragraph("Asset", table_header_style),
        Paragraph("Qty", table_header_style),
        Paragraph("Acquisition Date", table_header_style),
        Paragraph("Cost Basis (USD)", table_header_style),
        Paragraph("Sale Date", table_header_style),
        Paragraph("Proceeds (USD)", table_header_style),
        Paragraph("Gain / Loss", table_header_style)
    ]
    
    matches_table_rows = [matches_header]
    
    for m in lot_matches:
        buy_date = m.get("buy_timestamp")
        if isinstance(buy_date, str):
            buy_date = buy_date.split("T")[0]
        elif isinstance(buy_date, datetime):
            buy_date = buy_date.strftime("%Y-%m-%d")
        else:
            buy_date = "N/A"
            
        sell_date = m.get("sell_timestamp")
        if isinstance(sell_date, str):
            sell_date = sell_date.split("T")[0]
        elif isinstance(sell_date, datetime):
            sell_date = sell_date.strftime("%Y-%m-%d")
        else:
            sell_date = "N/A"
            
        gain = float(m.get("gain_loss", 0.0))
        
        matches_table_rows.append([
            Paragraph(str(m.get("asset", "")), table_body_style),
            Paragraph(f"{float(m.get('amount', 0.0)):.4f}", table_body_style),
            Paragraph(buy_date, table_body_style),
            Paragraph(f"${float(m.get('cost_basis', 0.0)):,.2f}", table_body_style),
            Paragraph(sell_date, table_body_style),
            Paragraph(f"${float(m.get('proceeds', 0.0)):,.2f}", table_body_style),
            Paragraph(f"${gain:,.2f}", table_body_bold_style if gain >= 0 else ParagraphStyle('RedText2', parent=table_body_bold_style, textColor=HexColor('#EF4444')))
        ])
        
    # Standard column widths totaling 6.0 inches (to fit standard letter printable area of 7.0 inches)
    matches_table = Table(
        matches_table_rows,
        colWidths=[0.8*inch, 0.8*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.0*inch],
        repeatRows=1
    )
    matches_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#0b0f15')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(matches_table)
    
    # Add page break and Legal Disclaimer
    elements.append(PageBreak())
    
    disclaimer_header_style = ParagraphStyle(
        'DisclaimerHeading',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=HexColor('#0b0f15'),
        spaceBefore=15,
        spaceAfter=15,
        keepWithNext=True
    )
    disclaimer_body_style = ParagraphStyle(
        'DisclaimerBody',
        fontName='Helvetica',
        fontSize=8.5,
        textColor=HexColor('#475569'),
        leading=12.5,
        spaceAfter=10
    )
    
    elements.append(Paragraph("Legal Disclaimer", disclaimer_header_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    disclaimer_paragraphs = [
        "This tax report is generated automatically by Declairo based on transaction data provided by the user. Declairo is a software tool and does not provide tax, legal, or financial advice.",
        "Cryptocurrency tax regulations vary by jurisdiction and may change over time. The accuracy and completeness of this report depend on the accuracy of the imported transaction data and selected calculation settings.",
        "Users are responsible for reviewing all calculations and are strongly encouraged to consult a qualified tax professional before filing any tax documents.",
        "Declairo assumes no responsibility or liability for any errors, omissions, tax obligations, penalties, or losses resulting from the use of this report or software."
    ]
    
    for para in disclaimer_paragraphs:
        elements.append(Paragraph(para, disclaimer_body_style))
        
    # Build Document
    doc.build(elements, canvasmaker=WrappedNumberedCanvas)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
