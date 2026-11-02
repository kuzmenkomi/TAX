"""Incoming/outgoing wallet classification and fee units."""
from unittest.mock import Mock

import pytest

from app.ingestion import wallet_importer as importer


ADDRESS = "0x" + "a" * 40


def test_evm_import_keeps_outgoing_gas_and_token_decimals(monkeypatch):
    def get(url, params, **kwargs):
        if params["action"] == "txlist":
            data = [
                {"timeStamp": "1700000000", "value": str(10**18), "to": "other", "from": ADDRESS,
                 "hash": "out", "gasUsed": "21000", "gasPrice": "1000000000"},
                {"timeStamp": "1700000001", "value": str(2 * 10**18), "to": ADDRESS, "from": "other", "hash": "in"},
                {"value": "0"},
            ]
        else:
            data = [{"timeStamp": "1700000002", "value": "1500000", "tokenDecimal": "6", "tokenSymbol": "usdc",
                     "to": ADDRESS, "from": "other", "hash": "token"}]
        result = Mock()
        result.json.return_value = {"status": "1", "result": data}
        return result
    monkeypatch.setattr(importer.requests, "get", get)
    frame = importer.import_wallet(ADDRESS, etherscan_api_key="demo-only")
    assert frame["type"].tolist() == ["TRANSFER", "RECEIVE", "RECEIVE"]
    assert frame["amount"].tolist() == [1, 2, 1.5]
    assert frame["fee"].tolist() == [0.000021, 0, 0]
    assert frame.iloc[-1]["external_id"] == "token_erc20"


def test_solana_negative_balance_change_is_outgoing(monkeypatch):
    address = "A" * 32
    response = Mock()
    response.json.return_value = [
        {"changeAmount": {address: -2000000000}, "blockTime": 1700000000, "fee": 5000, "txHash": "out"},
        {"changeAmount": {address: 1000000000}, "blockTime": 1700000001, "fee": 0, "txHash": "in"},
        {"changeAmount": {}},
    ]
    monkeypatch.setattr(importer.requests, "get", Mock(return_value=response))
    frame = importer.import_wallet(address)
    assert frame["type"].tolist() == ["TRANSFER", "RECEIVE"]
    assert frame["amount"].tolist() == [2, 1]
    assert frame.iloc[0]["fee"] == 0.000005


@pytest.mark.parametrize("address", [ADDRESS, "A" * 32])
def test_wallet_api_timeout_returns_empty_frame(monkeypatch, address):
    monkeypatch.setattr(importer.requests, "get", Mock(side_effect=TimeoutError("offline")))
    assert importer.import_wallet(address).empty


def test_invalid_addresses_and_networks_are_rejected():
    with pytest.raises(ValueError):
        importer.import_wallet("invalid")
    with pytest.raises(ValueError):
        importer.EVMImporter("unsupported")
