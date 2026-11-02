from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


CSV_CONTENT = """timestamp,asset,type,amount,fee,price,total_value,from_wallet,to_wallet
2026-01-01 00:00:00,BTC,BUY,0.10,0.0,95000,9500,Exchange,Wallet
2026-01-02 00:00:00,ETH,BUY,1.00,0.0,3200,3200,Exchange,Wallet
2026-01-03 00:00:00,SOL,BUY,5.00,0.0,180,900,Exchange,Wallet
2026-01-04 00:00:00,BTC,SELL,0.02,0.0,97000,1940,Wallet,Exchange
2026-01-05 00:00:00,ETH,SELL,0.25,0.0,3400,850,Wallet,Exchange
"""


def test_same_csv_can_be_reimported_after_run_deletion():
    with TestClient(app) as client:
        first = client.post(
            "/api/v1/analyze-upload",
            data={"format": "native", "accounting_method": "FIFO"},
            files={"file": ("test.csv", CSV_CONTENT, "text/csv")},
        )
        assert first.status_code == 200, first.text
        first_payload = first.json()
        assert first_payload["status"] == "ok"
        assert first_payload["rows_processed"] == 5
        assert first_payload["analysis_run_id"] is not None

        run_id = first_payload["analysis_run_id"]

        deleted = client.delete(f"/api/v1/br/runs/{run_id}")
        assert deleted.status_code == 200, deleted.text

        second = client.post(
            "/api/v1/analyze-upload",
            data={"format": "native", "accounting_method": "FIFO"},
            files={"file": ("test.csv", CSV_CONTENT, "text/csv")},
        )
        assert second.status_code == 200, second.text
        second_payload = second.json()
        assert second_payload["status"] == "ok"
        assert second_payload["duplicate"] is False
        assert second_payload["rows_processed"] == 5
        assert second_payload["analysis_run_id"] is not None

        runs = client.get("/api/v1/br/runs")
        assert runs.status_code == 200, runs.text
        payload = runs.json()
        assert len(payload["runs"]) == 1
        assert payload["runs"][0]["run_id"] == second_payload["analysis_run_id"]
        assert payload["runs"][0]["rows_processed"] == 5
