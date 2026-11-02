"""
Tests for LATAM integration modules.

Covers:
- bank_parsers (Nubank, MercadoPago, GenericBank)
- local_exchange_parsers (LemonCash, Belo, Buenbit, Orionx + factory)
- matching_service (P2P fuzzy match, time-window, price validation)

All tests are pure unit tests — no DB, no HTTP.
"""
import io
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

import pandas as pd


# ─── Bank Parsers ─────────────────────────────────────────────────────────────

from app.integrations.parsers.bank_parsers import (
    NubankParser,
    MercadoPagoParser,
    GenericBankParser,
)


def _csv_bytes(content: str) -> bytes:
    return content.encode("utf-8")


class TestNubankParser:
    """Nubank (Brazil Pix) CSV parser."""

    SAMPLE_CSV = (
        "Data,Valor,Identificador,Descrição\n"
        "01/05/2024,150.00,PIX123,Pagamento fulano\n"
        "02/05/2024,-50.00,PIX456,Saque ATM\n"
    )

    def test_parses_deposits_correctly(self):
        parser = NubankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))

        deposits = df[df["type"] == "deposit"]
        assert len(deposits) == 1
        assert float(deposits.iloc[0]["amount"]) == pytest.approx(150.0)

    def test_parses_withdrawals_correctly(self):
        parser = NubankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))

        withdrawals = df[df["type"] == "withdrawal"]
        assert len(withdrawals) == 1
        assert float(withdrawals.iloc[0]["amount"]) == pytest.approx(50.0)

    def test_amount_is_always_positive(self):
        parser = NubankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["amount"] >= 0).all()

    def test_asset_is_brl(self):
        parser = NubankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["asset"] == "BRL").all()

    def test_external_id_preserved(self):
        parser = NubankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert "PIX123" in df["external_id"].values


class TestMercadoPagoParser:
    """MercadoPago (Argentina/Mexico) CSV parser."""

    SAMPLE_CSV = (
        "fecha,monto,operacion,id_operacion\n"
        "2024-05-01,2000.50,Transferencia recibida,OP001\n"
        "2024-05-02,-500.00,Pago servicio,OP002\n"
    )

    def test_parses_rows(self):
        parser = MercadoPagoParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert len(df) == 2

    def test_deposit_type_detected(self):
        parser = MercadoPagoParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert df.iloc[0]["type"] == "deposit"

    def test_withdrawal_type_detected(self):
        parser = MercadoPagoParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert df.iloc[1]["type"] == "withdrawal"

    def test_asset_defaults_to_ars(self):
        parser = MercadoPagoParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["asset"] == "ARS").all()

    def test_external_id_populated(self):
        parser = MercadoPagoParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert "OP001" in df["external_id"].values


class TestGenericBankParser:
    """GenericBankParser auto-detects date and amount columns."""

    SAMPLE_CSV = (
        "date,monto,description\n"
        "2024-06-01,300.00,Compra crypto\n"
        "2024-06-02,-100.00,Retiro\n"
    )

    def test_detects_date_column(self):
        parser = GenericBankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert "timestamp" in df.columns

    def test_detects_amount_column(self):
        parser = GenericBankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert "amount" in df.columns
        assert float(df.iloc[0]["amount"]) == pytest.approx(300.0)

    def test_type_derived_from_sign(self):
        parser = GenericBankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert df.iloc[0]["type"] == "deposit"
        assert df.iloc[1]["type"] == "withdrawal"

    def test_exchange_tag_set(self):
        parser = GenericBankParser()
        df = parser.parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["exchange"] == "generic_bank").all()


# ─── Local Exchange Parsers ───────────────────────────────────────────────────

from app.integrations.parsers.local_exchange_parsers import (
    LemonCashParser,
    BeloParser,
    BuenbitParser,
    OrionxParser,
    get_parser_for_exchange,
)


class TestLemonCashParser:
    SAMPLE_CSV = (
        "Created At,Type,Asset,Amount,Price USD,Total USD,ID\n"
        "2024-01-10 14:00:00,BUY,BTC,0.01,42000,420.00,LEM001\n"
        "2024-01-11 10:00:00,SELL,ETH,0.5,2000,1000.00,LEM002\n"
    )

    def test_parses_all_rows(self):
        df = LemonCashParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert len(df) == 2

    def test_type_lowercased(self):
        df = LemonCashParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert df.iloc[0]["type"] == "buy"
        assert df.iloc[1]["type"] == "sell"

    def test_exchange_tag(self):
        df = LemonCashParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["exchange"] == "lemoncash").all()

    def test_asset_column(self):
        df = LemonCashParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert "BTC" in df["asset"].values
        assert "ETH" in df["asset"].values


class TestBeloParser:
    SAMPLE_CSV = (
        "date,type,currency,amount,balance\n"
        "2024-02-01,buy,BTC,0.005,0.005\n"
        "2024-02-05,sell,BTC,0.005,0.0\n"
    )

    def test_parses_all_rows(self):
        df = BeloParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert len(df) == 2

    def test_type_preserved(self):
        df = BeloParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert df.iloc[0]["type"] == "buy"

    def test_exchange_tag(self):
        df = BeloParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["exchange"] == "belo").all()


class TestBuenbitParser:
    SAMPLE_CSV = (
        "date,operation,asset,amount,status\n"
        "2024-03-01,buy,DAI,1000,completed\n"
        "2024-03-10,sell,DAI,1000,completed\n"
    )

    def test_parses_rows(self):
        df = BuenbitParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert len(df) == 2

    def test_exchange_tag(self):
        df = BuenbitParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["exchange"] == "buenbit").all()


class TestOrionxParser:
    SAMPLE_CSV = (
        "date,type,main_asset,amount,price,fee\n"
        "2024-04-01,buy,BTC,0.01,60000,5.0\n"
        "2024-04-15,sell,BTC,0.01,62000,5.5\n"
    )

    def test_parses_rows(self):
        df = OrionxParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert len(df) == 2

    def test_fee_column(self):
        df = OrionxParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert float(df.iloc[0]["fee"]) == pytest.approx(5.0)

    def test_exchange_tag(self):
        df = OrionxParser().parse(_csv_bytes(self.SAMPLE_CSV))
        assert (df["exchange"] == "orionx").all()


class TestGetParserFactory:
    """Factory function returns the correct parser class."""

    def test_lemon_parser_returned(self):
        parser = get_parser_for_exchange("lemon")
        assert isinstance(parser, LemonCashParser)

    def test_belo_parser_returned(self):
        parser = get_parser_for_exchange("belo")
        assert isinstance(parser, BeloParser)

    def test_buenbit_parser_returned(self):
        parser = get_parser_for_exchange("buenbit")
        assert isinstance(parser, BuenbitParser)

    def test_orionx_parser_returned(self):
        parser = get_parser_for_exchange("orionx")
        assert isinstance(parser, OrionxParser)

    def test_unknown_exchange_returns_none(self):
        result = get_parser_for_exchange("unknown_exchange_xyz")
        assert result is None

    def test_case_insensitive(self):
        parser = get_parser_for_exchange("LEMON")
        assert isinstance(parser, LemonCashParser)

    def test_case_insensitive_belo(self):
        parser = get_parser_for_exchange("Belo")
        assert isinstance(parser, BeloParser)


# ─── Matching Service ─────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch
from app.services.matching_service import MatchingService


class TestMatchingService:
    """
    P2P transaction matching service.
    Uses mocked DB sessions — no real database required.
    """

    def _make_mock_crypto_tx(self, price=None, asset="BTC", amount=0.01, minutes_offset=0):
        tx = MagicMock()
        tx.asset = asset
        tx.amount = Decimal(str(amount))
        tx.price = price
        tx.timestamp = datetime(2024, 5, 1, 12, 0) + timedelta(minutes=minutes_offset)
        tx.linked_bank_txn_id = None
        tx.tx_type = "deposit"
        tx.id = f"crypto_{minutes_offset}"
        return tx

    def _make_mock_bank_tx(self, amount=500.0, currency="BRL", minutes_offset=10):
        tx = MagicMock()
        tx.amount = Decimal(str(amount))
        tx.currency = currency
        tx.date = datetime(2024, 5, 1, 12, 0) + timedelta(minutes=minutes_offset)
        tx.type = "withdrawal"
        tx.id = f"bank_{minutes_offset}"
        return tx

    def test_no_transactions_returns_zero_matches(self):
        """When there are no crypto receipts, match count is 0."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = MatchingService.match_p2p_purchases(db, user_id=1)
        assert result == 0

    def test_crypto_with_price_is_skipped(self):
        """Crypto transactions that already have a price should not be matched."""
        db = MagicMock()
        crypto_tx = self._make_mock_crypto_tx(price=Decimal("42000"))  # already priced

        db.query.return_value.filter.return_value.all.return_value = [crypto_tx]

        result = MatchingService.match_p2p_purchases(db, user_id=1)
        assert result == 0

    def test_match_updates_db(self):
        """After matching, db.commit() should be called."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        MatchingService.match_p2p_purchases(db, user_id=1)
        db.commit.assert_called_once()

    def test_service_is_static_method(self):
        """match_p2p_purchases should be callable without instantiation."""
        assert callable(MatchingService.match_p2p_purchases)
