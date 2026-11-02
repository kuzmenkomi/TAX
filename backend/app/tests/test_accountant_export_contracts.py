"""Real CSV/PDF generation and lot-level accountant report totals."""
import csv
import io
import re
from datetime import datetime
from decimal import Decimal as D
from types import SimpleNamespace

import pandas as pd
import pytest

from app.exporters.transaction_matcher import TransactionMatcher
from app.services import export_task


@pytest.mark.parametrize("method,cost,gain", [("match_fifo", "200", "250"),
    ("match_lifo", "250", "200"), ("match_average_cost", "225", "225")])
def test_accountant_lot_matching_conserves_sold_quantity_and_proceeds(method, cost, gain):
    transactions = [
        {"id": 1, "date": datetime(2023, 1, 1), "type": "buy", "quantity": 1, "price": 100},
        {"id": 2, "date": datetime(2024, 6, 1), "type": "buy", "quantity": 1, "price": 200},
        {"id": 3, "date": datetime(2025, 1, 1), "type": "sell", "quantity": 1.5, "price": 300},
    ]
    matcher = TransactionMatcher("BTC", transactions)
    assert matcher.get_summary()["total_trades"] == 0
    assert matcher.export_to_csv() == "No trades to export\n"
    trades = getattr(matcher, method)()
    assert sum(t.quantity for t in trades) == D("1.5")
    summary = matcher.get_summary()
    assert summary["total_cost"] == D(cost)
    assert summary["total_proceeds"] == D("450")
    assert summary["total_gain_loss"] == D(gain)
    assert matcher.get_unmatched_quantity()["unmatched_holding"] == D("0.5")
    assert "Gain/Loss" in matcher.export_to_csv()
    assert all(t.gain_loss_percentage > 0 for t in trades)
    assert transactions[0]["quantity"] == 1


@pytest.fixture
def report_input(monkeypatch, tmp_path):
    from app.routers.v1 import exports
    path = tmp_path / "transactions.csv"
    pd.DataFrame([
        {"timestamp": "2025-01-01", "type": "BUY", "asset": "BTC", "amount": 1, "price": 100, "fee": 0, "id": 1},
        {"timestamp": "2025-02-01", "type": "SELL", "asset": "BTC", "amount": 1, "price": 200, "fee": 0.01, "id": 2},
    ]).to_csv(path, index=False)
    monkeypatch.setattr(exports, "_get_csv_path", lambda run: str(path))
    monkeypatch.setattr(exports, "_get_summary", lambda run: {"pnl": {
        "realized_pnl_by_asset": {"BTC": 98, "ETH": -5},
        "lot_matches": [{"sell_tx_id": 2, "asset": "BTC", "gain_loss": 98}],
    }})
    return SimpleNamespace(id=1)


def test_csv_report_uses_realized_gain_from_matched_lots(report_input):
    output = export_task.generate_csv_export(report_input, None)
    rows = list(csv.DictReader(io.StringIO(output)))
    assert len(rows) == 2
    assert rows[0]["Realized P&L"] == "0.00"
    assert rows[1]["Realized P&L"] == "98.00"
    assert rows[1]["Fee"] == "0.01"


def test_pdf_report_produces_complete_multipage_document(report_input):
    user = SimpleNamespace(full_name="Demo User", email="demo@example.com", jurisdiction_code="US")
    result = export_task.generate_pdf_export(report_input, None, user)
    assert result.startswith(b"%PDF-") and result.rstrip().endswith(b"%%EOF")
    page_count = re.search(rb"/Count\s+(\d+)", result)
    assert page_count is not None and int(page_count[1]) >= 3
