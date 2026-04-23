"""
Tax form exporters for accountant filing.

- Form 8949 (US): Sales of Capital Assets
- IRPF (Brazil): Income declaration XML
- LATAM (General): Generic CSV declaration in local currency (e.g., SAT Mexico, ARS, COP)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pandas as pd


def export_to_form_8949_csv(
    df: pd.DataFrame, 
    matches: list[dict[str, Any]], 
    output_dir: str = "output"
) -> dict[str, str]:
    """
    Export to Form 8949 (Sales of Capital Assets) CSV format.
    
    Form 8949 requires:
    - Date acquired
    - Date sold  
    - Description of property
    - Proceeds (sale price)
    - Cost or basis
    - Gain or loss
    
    Output: dict with "form_8949_csv" path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    rows = []
    
    # Only include SELL/OUT/WITHDRAW transactions (disposition events)
    for idx, tx in df[df["type"].isin(["SELL", "OUT", "WITHDRAW"])].iterrows():
        timestamp = tx.get("timestamp")
        if pd.isna(timestamp):
            continue
            
        # Parse date
        try:
            if isinstance(timestamp, (int, float)):
                date_obj = pd.Timestamp(timestamp, unit='s')
            else:
                date_obj = pd.Timestamp(timestamp)
            date_sold = date_obj.strftime("%m/%d/%Y")
        except Exception:
            continue
        
        asset = str(tx.get("asset", "")).upper()
        amount = float(tx.get("amount", 0))
        price = float(tx.get("price", 0))
        fee = float(tx.get("fee", 0))
        total_value = float(tx.get("total_value", 0))
        
        # Proceeds = sale price - fee
        proceeds = (amount * price) - (fee * price)
        
        # Cost basis requires tracking which transaction was the purchase
        # For MVP, use avg_cost from match data if available, else estimate
        cost_basis = 0.0
        avg_cost_per_unit = 0.0
        
        # Try to find matching purchase in matches
        for match in matches:
            if match.get("sell_index") == idx and "avg_cost_for_sale" in match:
                cost_basis = float(match.get("avg_cost_for_sale", 0))
                break
        
        if cost_basis == 0:
            # Fallback: use previous price as cost basis (not accurate but better than 0)
            cost_basis = amount * price
        
        gain_loss = proceeds - cost_basis
        
        rows.append({
            "(a) Description": f"{asset}",
            "(b) Date acquired": "Various (See attached log)",
            "(c) Date sold or disposed": date_sold,
            "(d) Proceeds (sales price)": f"{proceeds:,.2f}",
            "(e) Cost or other basis": f"{cost_basis:,.2f}",
            "(f) Gain or (loss)": f"{gain_loss:,.2f}",
            "Notes": f"{amount:.8f} {asset} @ ${price:.2f}, fee: ${fee * price:.2f}",
        })
    
    # Save to CSV
    if rows:
        form_8949_df = pd.DataFrame(rows)
        form_8949_path = output_path / "form_8949.csv"
        form_8949_df.to_csv(form_8949_path, index=False)
    else:
        form_8949_path = output_path / "form_8949.csv"
        pd.DataFrame(rows).to_csv(form_8949_path, index=False)
    
    return {"form_8949_csv": str(form_8949_path)}


def export_to_irpf_xml(
    df: pd.DataFrame,
    matches: list[dict[str, Any]],
    user_email: str,
    output_dir: str = "output"
) -> dict[str, str]:
    """
    Export to IRPF (Imposto de Renda) XML format for Brazilian tax filing.
    
    Generates XML compatible with Receita Federal do Brasil's e-CAC software.
    Includes:
    - Bens e Direitos (Assets): open positions
    - Operações em Bolsa (Stock operations): all trades
    - Aluguels e Royalties: income from staking/interest
    
    Output: dict with "irpf_xml" path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create root XML element
    root = ET.Element("IRPF")
    root.set("versao", "1.0")
    root.set("gerado", datetime.now().isoformat())
    
    # Declaration info
    decl = ET.SubElement(root, "Declaracao")
    ET.SubElement(decl, "CPF").text = "***REDACTED***"  # User should fill this
    ET.SubElement(decl, "AnoCalendario").text = str(datetime.now().year)
    ET.SubElement(decl, "Email").text = user_email or ""
    
    # === BENS E DIREITOS: Current positions (unrealized) ===
    bens = ET.SubElement(root, "BensEDireitos")
    posicoes = df.groupby("asset").apply(lambda g: {
        "amount": g["amount"].sum() if g["type"].isin(["BUY", "RECEIVE", "DEPOSIT"]).any() else 0,
        "price": g[g["type"].isin(["BUY", "RECEIVE", "DEPOSIT"])]["price"].mean() if len(g[g["type"].isin(["BUY", "RECEIVE", "DEPOSIT"])]) > 0 else 0
    })
    
    for asset, pos_data in posicoes.items():
        if pos_data["amount"] <= 0:
            continue
        bem = ET.SubElement(bens, "Bem")
        ET.SubElement(bem, "Tipo").text = "Criptomoedas"
        ET.SubElement(bem, "Descricao").text = f"{pos_data['amount']:.8f} {asset}"
        ET.SubElement(bem, "Valor").text = f"{pos_data['amount'] * pos_data['price']:,.2f}"
        ET.SubElement(bem, "Situacao").text = "01"  # Posse/propriedade
    
    # === OPERAÇÕES EM BOLSA: All trades ===
    ops = ET.SubElement(root, "OperacoesEmBolsa")
    for idx, tx in df[df["type"].isin(["BUY", "SELL", "OUT"])].iterrows():
        try:
            timestamp = tx.get("timestamp")
            if isinstance(timestamp, (int, float)):
                date_obj = pd.Timestamp(timestamp, unit='s')
            else:
                date_obj = pd.Timestamp(timestamp)
            date_str = date_obj.strftime("%d/%m/%Y")
        except Exception:
            continue
        
        op = ET.SubElement(ops, "Operacao")
        ET.SubElement(op, "Data").text = date_str
        ET.SubElement(op, "TipoOperacao").text = "C" if tx["type"] in ["BUY", "RECEIVE"] else "V"  # Compra/Venda
        ET.SubElement(op, "Ativo").text = str(tx["asset"]).upper()
        ET.SubElement(op, "Cantidad").text = f"{float(tx.get('amount', 0)):.8f}"
        ET.SubElement(op, "Valor").text = f"{float(tx.get('price', 0)):,.8f}"
        ET.SubElement(op, "Corretagem").text = f"{float(tx.get('fee', 0)) * float(tx.get('price', 0)):,.2f}"
    
    # === RENDIMENTOS TRIBUTADOS: Income from staking/interest ===
    rend = ET.SubElement(root, "RendimentosTributados")
    for idx, tx in df[df["type"].isin(["INTEREST", "STAKING"])].iterrows():
        try:
            timestamp = tx.get("timestamp")
            if isinstance(timestamp, (int, float)):
                date_obj = pd.Timestamp(timestamp, unit='s')
            else:
                date_obj = pd.Timestamp(timestamp)
            date_str = date_obj.strftime("%d/%m/%Y")
        except Exception:
            continue
        
        rendim = ET.SubElement(rend, "Rendimento")
        ET.SubElement(rendim, "Data").text = date_str
        ET.SubElement(rendim, "Tipo").text = "01"  # Income from cryptoassets
        ET.SubElement(rendim, "Descricao").text = f"{float(tx.get('amount', 0)):.8f} {tx['asset']}"
        ET.SubElement(rendim, "Valor").text = f"{float(tx.get('total_value', 0)):,.2f}"
        ET.SubElement(rendim, "Pais").text = "105"  # Brazil
    
    # Pretty print and save
    tree = ET.ElementTree(root)
    irpf_path = output_path / "irpf_declaracao.xml"
    tree.write(str(irpf_path), encoding="UTF-8", xml_declaration=True)
    
    return {"irpf_xml": str(irpf_path)}


def export_to_latam_tax_csv(
    df: pd.DataFrame,
    matches: list[dict[str, Any]],
    price_service: Any,
    output_dir: str = "output"
) -> dict[str, str]:
    """
    Generic LATAM CSV export following the "Landing Principle" (Principle of Sovereignty).
    Converts all values to the local currency on the day of the transaction.
    
    Used for:
    - Mexico (SAT)
    - Argentina (ARS Oficial)
    - Colombia (TRM)
    - etc.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    currency = price_service.quote_currency
    
    rows = []
    for idx, tx in df.iterrows():
        tx_type = str(tx.get("type", "")).upper()
        if tx_type not in ["SELL", "OUT", "TRADE", "INTEREST", "STAKING"]:
            continue
            
        timestamp = tx.get("timestamp")
        try:
            if isinstance(timestamp, (int, float)):
                date_obj = pd.Timestamp(timestamp, unit='s')
            else:
                date_obj = pd.Timestamp(timestamp)
            date_str = date_obj.strftime("%Y-%m-%d")
        except Exception:
            continue
            
        asset = str(tx.get("asset", "")).upper()
        amount = float(tx.get("amount", 0))
        price_usd = float(tx.get("price", 0))
        
        # Fetch local rate for the day using the new registry-based service
        ts_sec = date_obj.timestamp()
        local_rate = price_service.get_currency_rate(ts_sec)
        
        val_usd = float(tx.get("total_value", amount * price_usd))
        val_local = val_usd * local_rate
        
        # Fees also need conversion
        fee_usd = float(tx.get("fee", 0)) * price_usd
        fee_local = fee_usd * local_rate
        
        rows.append({
            "Fecha": date_str,
            "Concepto": f"{tx_type}: {asset}",
            "Activo": asset,
            "Cantidad": f"{amount:.8f}",
            "Precio (USD)": f"{price_usd:.8f}",
            f"Tasa Oficial (USD/{currency})": f"{local_rate:.4f}",
            f"Monto Total ({currency})": f"{val_local:.2f}",
            f"Comisión Deducible ({currency})": f"{fee_local:.2f}",
            "Tipo de Ingreso": "Acumulable" if tx_type in ["INTEREST", "STAKING"] else "Ganancia de Capital",
        })
        
    filename = f"tax_declaration_{currency.lower()}.csv"
    sat_path = output_path / filename
    if rows:
        pd.DataFrame(rows).to_csv(sat_path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(columns=["Fecha", "Concepto", f"Monto Total ({currency})"]).to_csv(sat_path, index=False)
        
    return {f"latam_{currency.lower()}_csv": str(sat_path)}


def export_to_mexico_sat_csv(
    df: pd.DataFrame,
    matches: list[dict[str, Any]],
    price_service: Any,
    output_dir: str = "output"
) -> dict[str, str]:
    """Wrapper for backward compatibility specifically for Mexico."""
    return export_to_latam_tax_csv(df, matches, price_service, output_dir)


def export_accounting_summary_csv(
    pnl_result: dict[str, Any],
    output_dir: str = "output"
) -> dict[str, str]:
    """
    High-level accounting summary for accountant review.
    
    Shows:
    - Total realized PnL by asset
    - Tax events count
    - Gas/fee summary
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    rows = []
    
    # Realized PnL by asset
    for asset, pnl in pnl_result.get("realized_pnl_by_asset", {}).items():
        rows.append({
            "Category": "Realized PnL",
            "Asset": asset,
            "Amount USD": f"{pnl:,.2f}",
        })
    
    # Tax summary
    rows.append({
        "Category": "Tax Summary",
        "Asset": "Total",
        "Amount USD": f"{pnl_result.get('total_realized_pnl_usd', 0):,.2f}",
    })
    rows.append({
        "Category": "Tax Summary",
        "Asset": "Taxable Events",
        "Amount USD": pnl_result.get("taxable_events_count", 0),
    })
    rows.append({
        "Category": "Expenses",
        "Asset": "Gas/Fees",
        "Amount USD": f"{pnl_result.get('total_gas_fees_usd', 0):,.2f}",
    })
    
    summary_df = pd.DataFrame(rows)
    summary_path = output_path / "accounting_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    
    return {"accounting_summary_csv": str(summary_path)}
