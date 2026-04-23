from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.accounting.avco_engine import compute_pnl_avco
from app.accounting.pricing import PriceService
from app.api.server import app, BACKEND_ROOT, RUNS_DIR
from app.tax.br_reports import compute_darf_projection, compute_monthly_sales_brl


def test_price_service_uses_ptax_when_enabled(monkeypatch):
    """PriceService(get_spot_price) должен брать PTAX при use_ptax=True и BRL-котировке."""

    called = {}

    def fake_get(url, params=None, timeout=0):
        called["url"] = url

        class Resp:
            def raise_for_status(self): ...

            def json(self):
                return {
                    "value": [
                        {
                            "cotacaoCompra": 5.0,
                            "cotacaoVenda": 5.2,
                        }
                    ]
                }

        return Resp()

    monkeypatch.setattr("app.accounting.pricing.requests.get", fake_get)

    svc = PriceService(quote_currency="BRL", use_ptax=True)
    # 2024‑01‑15 12:00 UTC
    ts = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc).timestamp()
    px = svc.get_spot_price("BTC", ts)

    # BTCUSDT ~ 0 в нашем фейке, но важно что PTAX запросился и множитель > 0
    assert "CotacaoDolarDia" in called["url"]
    # main thing: метод не падает и возвращает float
    assert isinstance(px, float)


def test_avco_fees_affect_cost_basis_and_proceeds():
    """Комиссия при покупке увеличивает cost basis, при продаже уменьшает чистую выручку."""
    df = pd.DataFrame(
        [
            # BUY 1 BTC по 100 с комиссией 10 → cost basis = 110
            {"timestamp": 1, "type": "BUY", "asset": "BTC", "amount": 1.0, "fee": 0.1, "price": 100.0},
            # SELL 1 BTC по 150 с комиссией 5 → proceeds = 145
            {"timestamp": 2, "type": "SELL", "asset": "BTC", "amount": 1.0, "fee": (5.0 / 150.0), "price": 150.0},
        ]
    )
    out = compute_pnl_avco(df)
    # cost basis 110, proceeds 145 → PnL = 35
    assert pytest.approx(out["total_realized_pnl_usd"], rel=1e-6) == 35.0


def test_monthly_sales_and_darf_projection_threshold():
    """DARF должен считаться только если продажи > 35k и прибыль положительная."""
    dates = pd.to_datetime(
        [
            "2024-05-10",
            "2024-05-15",
        ]
    )
    df = pd.DataFrame(
        [
            {"timestamp": dates[0], "type": "SELL", "asset": "BTC", "amount": 0.5, "price": 40000.0},
            {"timestamp": dates[1], "type": "SELL", "asset": "BTC", "amount": 0.5, "price": 40000.0},
        ]
    )
    monthly = compute_monthly_sales_brl(df)
    # Май: 0.5*40k + 0.5*40k = 40k
    assert pytest.approx(monthly["2024-05"], rel=1e-6) == 40000.0

    pnl = {"total_realized_pnl_usd": 10000.0}
    darf = compute_darf_projection(pnl, monthly, tax_rate=0.15, threshold_brl=35000.0)
    assert darf is not None
    assert darf["taxable"] is True
    assert pytest.approx(darf["amount_brl"], rel=1e-6) == 1500.0
    assert darf["code"] == "4600"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Минимальный TestClient для smoke‑теста /exports/gcap/{run_id}."""
    db_path = tmp_path / "tax_app.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # Гарантируем, что каталоги под RUNS_DIR существуют
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return TestClient(app)


def test_export_gcap_smoke(client):
    # Создаём фейковый CSV для AnalysisRun
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RUNS_DIR / "1_fake.csv"
    df = pd.DataFrame(
        [
            {"timestamp": "2024-05-10", "type": "SELL", "asset": "BTC", "amount": 0.1, "price": 40000.0, "fee": 0.001},
        ]
    )
    df.to_csv(csv_path, index=False)

    # Вставляем минимальную запись AnalysisRun напрямую в БД.
    from app.db import engine
    from app.models import AnalysisRun, User
    from sqlalchemy.orm import Session

    rel = str(csv_path.relative_to(BACKEND_ROOT)).replace("\\", "/")

    with Session(engine) as s:
        email = f"test_{uuid4().hex}@example.com"
        user = User(email=email, hashed_password="x")
        s.add(user)
        s.flush()
        run = AnalysisRun(user_id=user.id, csv_rel_path=rel, summary_json="{}")
        s.add(run)
        s.commit()
        run_id = run.id
        user_id = user.id

    # Endpoint защищен auth; подменяем dependency, чтобы тест ходил как владелец run.
    from app.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: User(
        id=user_id, email=email, hashed_password="x"
    )
    try:
        resp = client.get(f"/exports/gcap/{run_id}")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert b"Data da Operacao" in resp.content
    finally:
        app.dependency_overrides.pop(get_current_user, None)

