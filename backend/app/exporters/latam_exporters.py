import io
import csv
import json
from datetime import datetime
from typing import Any, List

def export_afip_csv(lot_matches: List[dict[str, Any]]) -> io.BytesIO:
    """
    Argentina (AFIP) compatible export.
    Expects lot_matches with USD values.
    Note: Real implementation should convert USD to ARS using official 'Dólar MEP' or 'Dólar Cable' rates.
    """
    buffer = io.BytesIO()
    writer = csv.writer(io.TextIOWrapper(buffer, encoding='utf-8', write_through=True))
    
    writer.writerow(["Fecha Compra", "Fecha Venta", "Activo", "Cantidad", "Costo (USD)", "Venta (USD)", "Resultado (USD)"])
    
    for m in lot_matches:
        writer.writerow([
            m["buy_timestamp"].strftime("%d/%m/%Y"),
            m["sell_timestamp"].strftime("%d/%m/%Y"),
            m["asset"],
            f"{m['amount']:.8f}",
            f"{m['cost_basis']:.2f}",
            f"{m['proceeds']:.2f}",
            f"{m['gain_loss']:.2f}"
        ])
    
    buffer.seek(0)
    return buffer

def export_sat_mexico_json(lot_matches: List[dict[str, Any]]) -> io.BytesIO:
    """
    Mexico (SAT) compatible JSON export.
    """
    data = []
    for m in lot_matches:
        data.append({
            "fecha_adquisicion": m["buy_timestamp"].isoformat(),
            "fecha_enajenacion": m["sell_timestamp"].isoformat(),
            "activo": m["asset"],
            "monto": m["amount"],
            "costo_comprobado": round(m["cost_basis"], 2),
            "ingreso_enajenacion": round(m["proceeds"], 2),
            "ganancia_perdida": round(m["gain_loss"], 2)
        })
    
    content = json.dumps(data, indent=2)
    return io.BytesIO(content.encode('utf-8'))

def export_sii_chile_csv(lot_matches: List[dict[str, Any]]) -> io.BytesIO:
    """
    Chile (SII) compatible export.
    """
    buffer = io.BytesIO()
    writer = csv.writer(io.TextIOWrapper(buffer, encoding='utf-8', write_through=True), delimiter=';')
    
    writer.writerow(["Activo", "Cantidad", "Fecha Adquisicion", "Valor Costo", "Fecha Enajenacion", "Valor Venta", "Mayor Valor"])
    
    for m in lot_matches:
        writer.writerow([
            m["asset"],
            str(m["amount"]).replace('.', ','),
            m["buy_timestamp"].strftime("%Y-%m-%d"),
            str(round(m["cost_basis"], 2)).replace('.', ','),
            m["sell_timestamp"].strftime("%Y-%m-%d"),
            str(round(m["proceeds"], 2)).replace('.', ','),
            str(round(m["gain_loss"], 2)).replace('.', ',')
        ])
    
    buffer.seek(0)
    return buffer

def export_dian_colombia_csv(lot_matches: List[dict[str, Any]]) -> io.BytesIO:
    """
    Colombia (DIAN) compatible export.
    """
    buffer = io.BytesIO()
    writer = csv.writer(io.TextIOWrapper(buffer, encoding='utf-8', write_through=True))
    
    writer.writerow(["Activo", "Unidades", "Costo Fiscal", "Valor Realizacion", "Ganancia/Perdida"])
    
    for m in lot_matches:
        writer.writerow([
            m["asset"],
            f"{m['amount']:.8f}",
            f"{m['cost_basis']:.2f}",
            f"{m['proceeds']:.2f}",
            f"{m['gain_loss']:.2f}"
        ])
    
    buffer.seek(0)
    return buffer
