"""Contract checks for the optional offline bank connectors and their manager."""
from datetime import datetime
from unittest.mock import Mock

import pytest

from app.advanced_tax.services.bank_connector import BankType, BankConnectorFactory, BankManager, TransactionType


@pytest.mark.parametrize("bank,credentials,currency", [
    (BankType.NUBANK, {"email": "demo@example.com", "password": "demo-only"}, "BRL"),
    (BankType.MERCADO_PAGO, {"api_token": "demo-only"}, "ARS"),
    (BankType.LEMON, {"api_key": "demo-only"}, "MXN"),
])
def test_connector_lifecycle_keeps_credentials_out_of_account_output(bank, credentials, currency):
    connector = BankConnectorFactory.create(bank)
    assert connector.get_accounts() == []
    assert connector.get_transactions("missing", datetime(2025, 1, 1), datetime(2025, 2, 1)) == []
    assert connector.authenticate({}) is False
    manager = BankManager()
    assert manager.connect_bank(bank, {}) is None
    account = manager.connect_bank(bank, credentials)
    assert account.currency == currency
    output = manager.get_connected_banks()[0]
    assert len(output["account_number"]) == 4
    assert not {"api_key", "api_secret", "refresh_token"}.intersection(output)
    result = manager.sync_all()
    assert result[account.id][1] is True
    assert account.sync_status == "synced" and account.last_sync is not None
    deposits = manager.get_deposit_transactions()
    assert deposits and all(row.type == TransactionType.DEPOSIT for row in deposits)
    assert deposits[0].to_dict()["currency"] == currency


def test_failed_sync_does_not_advance_last_sync(monkeypatch):
    manager = BankManager()
    account = manager.connect_bank(BankType.LEMON, {"api_key": "demo-only"})
    connector = manager.connectors[BankType.LEMON]
    monkeypatch.setattr(connector, "get_transactions", Mock(side_effect=RuntimeError("offline")))
    assert manager.sync_all()[account.id] == (0, False)
    assert account.last_sync is None
    assert account.sync_status == "error"
    manager.connectors.clear()
    assert manager.sync_all()[account.id] == (0, False)
    assert manager.get_deposit_transactions() == []


def test_unsupported_bank_is_not_connected():
    manager = BankManager()
    assert manager.connect_bank(BankType.CUSTOM_API, {}) is None
    assert manager.get_connected_banks() == []
