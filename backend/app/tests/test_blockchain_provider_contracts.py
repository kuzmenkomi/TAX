"""Explorer parsing, unit conversion and outage behavior without network access."""
from unittest.mock import Mock

import pytest

from app.integrations import blockchain_explorer as explorers


def respond(payload):
    result = Mock()
    result.json.return_value = payload
    return result


@pytest.mark.parametrize("chain,asset", [("ethereum", "eth"), ("polygon", "matic"), ("bsc", "bnb")])
def test_evm_native_token_nft_and_balance(monkeypatch, chain, asset):
    def get(url, params=None, **kwargs):
        action = params["action"]
        if action == "balance":
            return respond({"result": str(2 * 10**18)})
        if action == "txlist":
            rows = [{"timeStamp": "1700000000", "value": str(10**18), "from": "0xA", "to": "0xB", "hash": "native"},
                    {"timeStamp": "bad", "value": "bad"}]
        elif action == "tokentx":
            rows = [{"timeStamp": "1700000001", "value": "1500000", "tokenDecimal": "6", "tokenSymbol": "USDC", "hash": "token"}]
        else:
            rows = [{"timeStamp": "1700000002", "tokenSymbol": "ART", "tokenID": "7", "hash": "nft"}]
        return respond({"result": rows})
    monkeypatch.setattr(explorers.requests, "get", get)
    explorer = explorers.get_explorer(chain)
    frame = explorer.get_transactions("0xA", start_block=10)
    assert frame["type"].tolist() == ["TRANSFER", "TOKEN_TRANSFER", "NFT_TRANSFER"]
    assert frame["amount"].tolist() == [1, 1.5, 1]
    assert frame.iloc[2]["external_id"] == "nft:7"
    assert explorer.get_balance("0xA") == {asset: 2}


def test_bitcoin_satoshi_conversion_and_empty_transaction(monkeypatch):
    def get(url, **kwargs):
        if url.endswith("/addresses/wallet"):
            return respond({"data": {"wallet": {"balance": 200000000, "transactions": ["missing", "tx"]}}})
        if url.endswith("/missing"):
            return respond({"data": {}})
        return respond({"data": {"tx": {"block_time": 1700000000,
            "inputs": [{"addresses": ["wallet"], "value": 100000000, "recipient": "destination"}],
            "outputs": [{"addresses": ["different"], "value": 50000000}]}}})
    monkeypatch.setattr(explorers.requests, "get", get)
    explorer = explorers.get_explorer("btc")
    assert explorer.get_balance("wallet") == {"btc": 2}
    frame = explorer.get_transactions("wallet")
    assert len(frame) == 1
    assert frame.iloc[0]["amount"] == 1
    assert frame.iloc[0]["from_wallet"] == "wallet"


def test_solana_native_token_and_balance(monkeypatch):
    def get(url, **kwargs):
        if "solTransfers" in url:
            return respond([{"blockTime": 1700000000, "lamport": 2000000000, "src": "sender", "dst": "wallet", "txHash": "sol"}])
        if "tokenTransfers" in url:
            return respond([{"blockTime": 1700000001, "tokenAmount": 5, "tokenSymbol": "USDC", "txHash": "token"}])
        return respond({"solBalance": 3000000000})
    monkeypatch.setattr(explorers.requests, "get", get)
    explorer = explorers.get_explorer("sol")
    frame = explorer.get_transactions("wallet")
    assert frame["amount"].tolist() == [2, 5]
    assert frame["asset"].tolist() == ["SOL", "USDC"]
    assert explorer.get_balance("wallet") == {"sol": 3}


def test_tron_native_units_and_timestamps(monkeypatch):
    def get(url, **kwargs):
        if "token_trc20" in url:
            return respond([{"block_timestamp": 1700000001000, "quant": 5, "token_name": "USDT", "transaction_id": "token"}])
        if url.endswith("/transactions"):
            return respond([{"block_timestamp": 1700000000000, "trx": 2000000, "hash": "native"}])
        return respond({"balance": 3000000})
    monkeypatch.setattr(explorers.requests, "get", get)
    explorer = explorers.get_explorer("trx")
    frame = explorer.get_transactions("wallet")
    assert frame["amount"].tolist() == [2, 5]
    assert frame.iloc[0]["timestamp"].year == 2023
    assert explorer.get_balance("wallet") == {"trx": 3}


@pytest.mark.parametrize("chain", ["ethereum", "bitcoin", "solana", "tron"])
def test_explorer_outage_returns_typed_empty_results(monkeypatch, chain):
    monkeypatch.setattr(explorers.requests, "get", Mock(side_effect=TimeoutError("offline")))
    explorer = explorers.get_explorer(chain)
    assert explorer.get_transactions("wallet").empty
    assert "external_id" in explorers.fetch_wallet_transactions("wallet", chain).columns
    assert explorer.get_balance("wallet") == {}


def test_unknown_network_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        explorers.get_explorer("unknown")
