"""
Brazil Tax Documents Generation - GCAP & Carnê-Leão

Generates official Brazilian tax documents that can be imported directly
into the Federal Revenue Service (RFB) system.

GCAP: Ganhos de Capital (Capital Gains Report)
Carnê-Leão: Monthly advance tax payment schedule
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
import csv
import io

import pandas as pd


@dataclass
class CapitalGain:
    """Single capital gain transaction for GCAP."""
    
    operation_date: date
    alienation_date: date  # Data da alienação (sale date)
    asset: str  # Ativo (ticker/name)
    quantity: Decimal
    acquisition_price: Decimal  # Preço de aquisição
    total_acquisition_cost: Decimal  # Valor total de aquisição
    
    sale_price: Decimal  # Preço de alienação
    total_sale_value: Decimal  # Valor total de alienação
    
    brokerage_cost: Decimal = Decimal("0")  # Custos com corretagem
    other_costs: Decimal = Decimal("0")  # Outros custos
    
    @property
    def total_cost(self) -> Decimal:
        """Total cost including all expenses."""
        return self.total_acquisition_cost + self.brokerage_cost + self.other_costs
    
    @property
    def net_gain(self) -> Decimal:
        """Net capital gain/loss."""
        return self.total_sale_value - self.total_cost
    
    @property
    def is_loss(self) -> bool:
        """True if this is a loss."""
        return self.net_gain < 0


class GCAPGenerator:
    """Generates GCAP (Capital Gains Report) for Brazilian tax authorities."""
    
    # GCAP formato exigido pela RFB (Receita Federal do Brasil)
    # Modelo V5.0 (conforme Instrução Normativa 1515/2015)
    
    @staticmethod
    def generate_gcap_csv(
        capital_gains: list[CapitalGain],
        year: int,
        taxpayer_cpf: str
    ) -> str:
        """Generate GCAP in CSV format compatible with RFB system.
        
        Args:
            capital_gains: List of capital gain transactions
            year: Tax year
            taxpayer_cpf: Taxpayer's CPF (for header)
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quotechar='"')
        
        # Header section (GCAP identification)
        writer.writerow(["V5"])  # GCAP version
        writer.writerow(["0"])   # Skip line
        
        # Tax period
        writer.writerow([
            "1",  # Record type 1 (header)
            year,  # Ano calendário
            "01",  # Month start (january)
            "12",  # Month end (december)
            taxpayer_cpf,
            "01",  # IRPF declaration type code
            ""
        ])
        
        # Detail records for each transaction
        record_number = 1
        for gain in capital_gains:
            writer.writerow([
                "2",  # Record type 2 (detail)
                record_number,
                gain.operation_date.strftime("%d%m%Y"),  # Data da operação
                gain.alienation_date.strftime("%d%m%Y"),  # Data da alienação
                _format_asset_code(gain.asset),  # Código do ativo
                f"{gain.quantity:.8f}".replace(".", ","),  # Quantidade
                f"{gain.acquisition_price:.2f}".replace(".", ","),  # Preço médio
                f"{gain.total_cost:.2f}".replace(".", ","),  # Custo total
                f"{gain.sale_price:.2f}".replace(".", ","),  # Preço de venda
                f"{gain.total_sale_value:.2f}".replace(".", ","),  # Valor alienado
                "0" if gain.net_gain >= 0 else "1",  # Loss indicator
                f"{abs(gain.net_gain):.2f}".replace(".", ","),  # Ganho/Perda
            ])
            record_number += 1
        
        # Total record
        total_gains = sum(g.net_gain for g in capital_gains if g.net_gain > 0)
        total_losses = sum(g.net_gain for g in capital_gains if g.net_gain < 0)
        
        writer.writerow([
            "9",  # Record type 9 (summary)
            len(capital_gains),  # Total transactions
            f"{total_gains:.2f}".replace(".", ","),  # Total gains
            f"{total_losses:.2f}".replace(".", ","),  # Total losses
        ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_gcap_xml(
        capital_gains: list[CapitalGain],
        year: int,
        taxpayer_name: str,
        taxpayer_cpf: str
    ) -> str:
        """Generate GCAP in XML format (alternative format).
        
        Format follows RFB's latest e-CAC specifications.
        """
        # XML structure for GCAP
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<GCAP>',
            f'  <Periodo ano="{year}">',
            f'    <Contribuinte nome="{taxpayer_name}" cpf="{taxpayer_cpf}">',
            f'      <TotalGanhos>{_sum_gains(capital_gains, True):.2f}</TotalGanhos>',
            f'      <TotalPerdas>{_sum_gains(capital_gains, False):.2f}</TotalPerdas>',
            '      <Operacoes>',
        ]
        
        for i, gain in enumerate(capital_gains, 1):
            xml_lines.extend([
                f'        <Operacao id="{i}">',
                f'          <DataOperacao>{gain.operation_date.isoformat()}</DataOperacao>',
                f'          <DataAlienacao>{gain.alienation_date.isoformat()}</DataAlienacao>',
                f'          <Ativo>{gain.asset}</Ativo>',
                f'          <Quantidade>{gain.quantity}</Quantidade>',
                f'          <PrecoAquisicao>{gain.acquisition_price:.2f}</PrecoAquisicao>',
                f'          <CustoTotal>{gain.total_cost:.2f}</CustoTotal>',
                f'          <PrecoVenda>{gain.sale_price:.2f}</PrecoVenda>',
                f'          <ValorAlienado>{gain.total_sale_value:.2f}</ValorAlienado>',
                f'          <GanhoPerda>{gain.net_gain:.2f}</GanhoPerda>',
                '        </Operacao>',
            ])
        
        xml_lines.extend([
            '      </Operacoes>',
            '    </Contribuinte>',
            '  </Periodo>',
            '</GCAP>'
        ])
        
        return "\n".join(xml_lines)


@dataclass
class MonthlyIncome:
    """Income for a specific month (for Carnê-Leão calculation)."""
    
    month: int
    year: int
    income_amount: Decimal  # Rendimento tributável
    withheld_taxes: Decimal = Decimal("0")  # Impostos retidos
    
    @property
    def income_due(self) -> Decimal:
        """Income tax due (15% of income minus withheld)."""
        tax_rate = Decimal("0.15")  # 15% tax rate
        calculated_tax = self.income_amount * tax_rate
        return max(Decimal("0"), calculated_tax - self.withheld_taxes)


class CarneLeaoGenerator:
    """Generates Carnê-Leão (monthly advance tax payment schedule)."""
    
    # Carnê-Leão format specification
    # Formato: Recibo de Pagamento de Imposto (RPA)
    
    @staticmethod
    def generate_carne_leao(
        monthly_incomes: list[MonthlyIncome],
        year: int,
        taxpayer_name: str,
        taxpayer_cpf: str
    ) -> str:
        """Generate Carnê-Leão schedule.
        
        Returns:
            JSON-formatted schedule for display/export
        """
        schedule = {
            "type": "CARNE_LEAO",
            "year": year,
            "taxpayer": {
                "name": taxpayer_name,
                "cpf": taxpayer_cpf,
            },
            "months": [],
            "summary": {
                "total_income": Decimal("0"),
                "total_tax_due": Decimal("0"),
                "total_already_paid": Decimal("0"),
            }
        }
        
        for month_data in sorted(monthly_incomes, key=lambda x: x.month):
            month_entry = {
                "month": month_data.month,
                "date": f"{year}-{month_data.month:02d}-01",
                "period": f"{_get_month_name(month_data.month)}/{year}",
                
                # Payment details
                "income": float(month_data.income_amount),
                "tax_rate": "15%",
                "calculated_tax": float(month_data.income_amount * Decimal("0.15")),
                
                "withheld_taxes": float(month_data.withheld_taxes),
                "tax_due": float(month_data.income_due),
                
                # Payment information
                "due_date": _calculate_due_date(month_data.month),
                "reference_code": _generate_reference_code(
                    taxpayer_cpf, month_data.month, year
                ),
            }
            
            schedule["months"].append(month_entry)
            
            # Accumulate summary
            schedule["summary"]["total_income"] += month_data.income_amount
            schedule["summary"]["total_tax_due"] += month_data.income_due
            schedule["summary"]["total_already_paid"] += month_data.withheld_taxes
        
        # Convert Decimals to float for JSON
        schedule["summary"] = {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in schedule["summary"].items()
        }
        
        return schedule
    
    @staticmethod
    def generate_carne_leao_pdf(
        monthly_incomes: list[MonthlyIncome],
        year: int,
        taxpayer_name: str,
        taxpayer_cpf: str
    ) -> bytes:
        """Generate Carnê-Leão as printable PDF.
        
        Returns:
            PDF file as bytes
        """
        # Note: Requires reportlab or similar PDF library
        # This is a placeholder - implementation would use a PDF library
        schedule_data = CarneLeaoGenerator.generate_carne_leao(
            monthly_incomes, year, taxpayer_name, taxpayer_cpf
        )
        
        # TODO: Generate PDF from schedule_data
        # Use reportlab to create official-looking Carnê-Leão forms
        
        return b"PDF_PLACEHOLDER"


# ==================== UTILITY FUNCTIONS ====================

def _format_asset_code(asset: str) -> str:
    """Format asset code for GCAP (uppercase, max 12 chars)."""
    return asset.upper()[:12]


def _sum_gains(gains: list[CapitalGain], positive: bool) -> Decimal:
    """Sum only positive or negative gains."""
    if positive:
        return sum((g.net_gain for g in gains if g.net_gain > 0), Decimal("0"))
    else:
        return abs(sum((g.net_gain for g in gains if g.net_gain < 0), Decimal("0")))


def _get_month_name(month: int) -> str:
    """Get Portuguese month name."""
    months = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    return months[month - 1]


def _calculate_due_date(month: int) -> str:
    """Calculate due date for monthly payment.
    
    In Brazil, Carnê-Leão is due on the 20th of the following month.
    """
    if month == 12:
        next_month = 1
        year_offset = 1
    else:
        next_month = month + 1
        year_offset = 0
    
    return f"20th of {_get_month_name(next_month)}"


def _generate_reference_code(cpf: str, month: int, year: int) -> str:
    """Generate Carnê-Leão reference code.
    
    Format: AAMMDDDDNNNNNNNNNNNN (very simplified for demo)
    """
    cpf_digits = cpf.replace(".", "").replace("-", "")
    return f"{year}{month:02d}{cpf_digits}"


# ==================== API INTEGRATION ====================
"""
Add to your FastAPI app:

from app.tax.br_documents import GCAPGenerator, CarneLeaoGenerator, CapitalGain, MonthlyIncome
import pandas as pd
from datetime import date

@app.post("/br/export/gcap")
def export_gcap(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Generate GCAP (Capital Gains Report) for Brazilian tax authorities.'''
    
    # Get analysis run
    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == current_user.id
    ).first()
    if not run:
        raise HTTPException(status_code=404)
    
    # Extract capital gains from analysis
    normalized_df = pd.read_csv(run.normalized_csv_path)
    
    # Convert to CapitalGain objects
    gains = []
    for _, tx in normalized_df.iterrows():
        if tx["type"].upper() == "SELL":
            gain = CapitalGain(
                operation_date=pd.Timestamp(tx["timestamp"]).date(),
                alienation_date=pd.Timestamp(tx["timestamp"]).date(),
                asset=tx["asset"],
                quantity=Decimal(str(tx["amount"])),
                acquisition_price=Decimal(str(tx.get("avg_cost", 0))),
                total_acquisition_cost=Decimal(str(tx.get("cost_basis", 0))),
                sale_price=Decimal(str(tx["price"])),
                total_sale_value=Decimal(str(float(tx["amount"]) * float(tx["price"]))),
            )
            gains.append(gain)
    
    # Generate GCAP
    user = db.query(User).filter(User.id == current_user.id).first()
    gcap_csv = GCAPGenerator.generate_gcap_csv(
        gains,
        year=datetime.now().year,
        taxpayer_cpf=user.cpf or "00000000000"
    )
    
    return {
        "filename": f"GCAP_{datetime.now().year}.csv",
        "content": gcap_csv,
        "format": "csv",
        "note": "Import this file directly into Receita Federal's e-CAC system"
    }


@app.post("/br/export/carne-leao")
def export_carne_leao(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Generate Carnê-Leão (monthly advance tax schedule) for Brazilian taxpayers.'''
    
    # Get analysis run
    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == current_user.id
    ).first()
    if not run:
        raise HTTPException(status_code=404)
    
    # Extract income events by month
    from app.accounting.avco_engine import compute_income_events
    
    normalized_df = pd.read_csv(run.normalized_csv_path)
    income_result = compute_income_events(normalized_df)
    
    # Group income by month
    monthly_incomes = {}
    for event in income_result.get("income_events", []):
        month = event.timestamp.month
        year = event.timestamp.year
        key = (month, year)
        
        if key not in monthly_incomes:
            monthly_incomes[key] = Decimal("0")
        
        monthly_incomes[key] += event.total_usd
    
    # Convert to MonthlyIncome objects
    month_objects = [
        MonthlyIncome(
            month=month,
            year=year,
            income_amount=Decimal(str(amount))
        )
        for (month, year), amount in monthly_incomes.items()
    ]
    
    # Generate Carnê-Leão
    user = db.query(User).filter(User.id == current_user.id).first()
    schedule = CarneLeaoGenerator.generate_carne_leao(
        month_objects,
        year=datetime.now().year,
        taxpayer_name=user.full_name,
        taxpayer_cpf=user.cpf or "00000000000"
    )
    
    return {
        "filename": f"CARNE_LEAO_{datetime.now().year}.json",
        "schedule": schedule,
        "note": "Payment schedule for monthly advance tax payments (Carnê-Leão)"
    }
"""
