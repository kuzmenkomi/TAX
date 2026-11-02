"""Verify exported totals and serialization independently of API routing."""
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pandas as pd
import pytest

from app.exporters.csv_exporter import CSVExporter
from app.exporters.xml_exporter import XMLExporter
from app.exporters import tax_exporter


@pytest.fixture
def trade_frame():
    return pd.DataFrame([
        {"timestamp": "2025-01-01", "asset": "BTC", "type": "BUY", "amount": 1, "price": 100, "fee": 0, "total_value": 100},
        {"timestamp": "2025-02-01", "asset": "BTC", "type": "SELL", "amount": 0.5, "price": 200, "fee": 0.01, "total_value": 100},
        {"timestamp": "2025-03-01", "asset": "ETH", "type": "STAKING", "amount": 1, "price": 50, "fee": 0, "total_value": 50},
    ])


@pytest.mark.parametrize("country,root", [("MX", "Declaracion"), ("BR", "DIRPF"), ("AR", "DeclaracionJurada"),
    ("CO", "TaxDeclaration"), ("PE", "TaxDeclaration"), ("CL", "TaxDeclaration"), ("XX", "TaxDeclaration")])
def test_xml_totals_country_routing_and_escaping(country, root):
    profile = SimpleNamespace(tax_id="ABC 123", tax_payer_name="A & B <Partners>", tax_address="Main 1")
    jurisdiction = SimpleNamespace(code=country)
    exporter = XMLExporter(profile, jurisdiction, 2025, {
        "capital_gains": {"amount": "1000", "tax": "150"},
        "ordinary_income": {"amount": "500", "tax": "50"}, "vat": {"tax": "10"}})
    output = exporter.generate()
    parsed = ET.fromstring(output)
    assert parsed.tag == root
    assert "A & B <Partners>" in "".join(parsed.itertext())
    assert exporter._get_tax_summary()["total_tax"] == D("210")
    assert exporter.get_filename() == f"tax_export_{country}_2025_ABC_123.xml"
    assert exporter.get_content_type().startswith("application/xml")


def test_csv_summary_and_transaction_detail():
    profile = SimpleNamespace(tax_id=None, tax_payer_name="Demo", tax_address=None, tax_advisor_name=None)
    jurisdiction = SimpleNamespace(code="XX", name="Demo", vat_rate=D("0.1"), filing_authority="Demo Authority", reporting_currency="USD")
    exporter = CSVExporter(profile, jurisdiction, 2025, {
        "capital_gains": {"amount": 1000, "tax": 150}, "ordinary_income": {"amount": 500, "tax": 50},
        "vat": {"tax": 10}, "vat_base": 100, "transactions": [{"date": "2025-01-01", "asset": "BTC", "quantity": 1}]})
    output = exporter.generate()
    assert "210.00" in output and "BTC" in output
    assert "Demo Authority" in output
    assert exporter.get_filename() == "tax_export_XX_2025_taxpayer.csv"
    assert exporter.get_content_type().startswith("text/csv")
    assert exporter._get_header_info()["currency"] == "USD"
    assert exporter._format_decimal(None) == "0.00"
    assert exporter._format_date(datetime(2025, 1, 2)) == "2025-01-02"


def test_disposition_csv_uses_matched_cost_basis_and_fees(trade_frame, tmp_path):
    result = tax_exporter.export_to_form_8949_csv(trade_frame, [{"sell_index": 1, "avg_cost_for_sale": 50}], str(tmp_path))
    frame = pd.read_csv(result["form_8949_csv"])
    assert len(frame) == 1
    assert float(frame.iloc[0]["(d) Proceeds (sales price)"]) == 98
    assert float(frame.iloc[0]["(e) Cost or other basis"]) == 50
    assert float(frame.iloc[0]["(f) Gain or (loss)"]) == 48


def test_latam_export_converts_proceeds_and_fees(trade_frame, tmp_path):
    prices = SimpleNamespace(quote_currency="MXN", get_currency_rate=lambda timestamp: 20)
    result = tax_exporter.export_to_mexico_sat_csv(trade_frame, [], prices, str(tmp_path))
    frame = pd.read_csv(result["latam_mxn_csv"])
    assert frame["Monto Total (MXN)"].tolist() == [2000, 1000]
    assert frame["Comisión Deducible (MXN)"].tolist() == [40, 0]
    empty = tax_exporter.export_to_latam_tax_csv(trade_frame.iloc[:1], [], prices, str(tmp_path))
    assert pd.read_csv(empty["latam_mxn_csv"]).empty


def test_irpf_xml_and_accounting_summary_are_readable(trade_frame, tmp_path):
    result = tax_exporter.export_to_irpf_xml(trade_frame, [], "demo@example.com", str(tmp_path))
    root = ET.parse(result["irpf_xml"]).getroot()
    assert root.findtext("Declaracao/Email") == "demo@example.com"
    assert len(root.findall("OperacoesEmBolsa/Operacao")) == 2
    assert root.findtext("RendimentosTributados/Rendimento/Valor") == "50.00"
    result = tax_exporter.export_accounting_summary_csv({"realized_pnl_by_asset": {"BTC": 48}, "total_realized_pnl_usd": 48,
        "taxable_events_count": 1, "total_gas_fees_usd": 2}, str(tmp_path))
    summary = pd.read_csv(result["accounting_summary_csv"])
    assert summary.iloc[0]["Asset"] == "BTC"
    assert float(summary.iloc[0]["Amount USD"]) == 48
