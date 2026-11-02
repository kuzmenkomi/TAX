"""Price parsing and caching with deterministic provider responses."""
from unittest.mock import Mock

import pytest

from app.accounting import pricing


def response(data):
    result = Mock()
    result.json.return_value = data
    return result


def test_historical_prices_are_cached_and_stablecoins_do_not_use_network(monkeypatch):
    get = Mock(return_value=response({"BTC": {"USD": 123.45}, "USD": 124}))
    monkeypatch.setattr(pricing.requests, "get", get)
    provider = pricing.CryptoCompareProvider(api_key="demo-key")
    assert provider.get_historical_price("btc", 1700000000) == 123.45
    assert provider.get_historical_price("BTC", 1700000000) == 123.45
    assert get.call_count == 1
    assert provider.get_current_price("BTC") == 124
    assert provider.get_current_price("USDC") == 1
    assert provider.get_historical_price("USDT", 1700000000) == 1
    assert provider.get_current_prices_batch(["BTC", "USDC"]) == {"btc": 124, "usdc": 1}
    get.return_value = response({"Response": "Error"})
    assert provider.get_historical_price("ETH", 1700000001) == 0


def test_realtime_batch_cache_and_last_price_on_outage(monkeypatch):
    get = Mock(return_value=response({"data": [{"symbol": "BTC", "priceUsd": "50000"}, {"symbol": "ETH", "priceUsd": "2000"}]}))
    monkeypatch.setattr(pricing.requests, "get", get)
    provider = pricing.CoinCapProvider()
    assert provider.get_current_prices_batch(["BTC", "ETH"]) == {"btc": 50000, "eth": 2000}
    assert provider.get_current_prices_batch(["ETH"]) == {"eth": 2000}
    assert get.call_count == 1
    get.side_effect = TimeoutError("offline")
    assert provider.get_current_price("BTC") == 50000
    assert provider.get_current_price("UNKNOWN") == 0
    assert provider.get_current_price("USDT") == 1


@pytest.mark.parametrize("provider,payload,expected", [
    (pricing.BanxicoProvider, {"bmx": {"series": [{"datos": [{"dato": "17.5"}]}]}}, 17.5),
    (pricing.BCBProvider, {"value": [{"cotacaoCompra": 5, "cotacaoVenda": 5.2}]}, 5.1),
    (pricing.SFCProvider, [{"valor": "4000"}], 4000),
    (pricing.BCRAProvider, {"oficial": {"value_avg": 850}}, 850),
])
def test_currency_provider_response_and_cache(monkeypatch, provider, payload, expected):
    monkeypatch.setenv("BANXICO_TOKEN", "demo-only")
    get = Mock(return_value=response(payload))
    monkeypatch.setattr(pricing.requests, "get", get)
    instance = provider()
    assert instance.get_rate(1700000000) == pytest.approx(expected)
    calls = get.call_count
    assert instance.get_rate(1700000010) == pytest.approx(expected)
    assert get.call_count == calls
    assert instance._get_day_str("invalid") == ""
    assert instance._get_day_str(1700000000000) == instance._get_day_str(1700000000)


def test_currency_provider_looks_back_over_non_trading_days(monkeypatch):
    provider = pricing.BCBProvider()
    fetch = Mock(side_effect=[0, 0, 5.0])
    monkeypatch.setattr(provider, "_fetch_rate", fetch)
    assert provider.get_rate(1700000000) == 5
    assert fetch.call_count == 3
    assert fetch.call_args.args[0] == 1700000000 - 2 * 86400


def test_price_service_converts_quotes_and_exposes_sources(monkeypatch):
    service = pricing.PriceService("BRL")
    monkeypatch.setattr(service.historical_provider, "get_historical_price", Mock(return_value=100))
    monkeypatch.setattr(service._currency_providers["BRL"], "get_rate", Mock(return_value=5))
    price, source = service.get_spot_price_with_source("BTC", 1700000000)
    assert price == 500
    assert "BCBProvider" in source and "CryptoCompare" in source
    assert pricing.PriceService("unsupported").quote_currency == "USD"
    monkeypatch.setattr(service.realtime_provider, "get_current_price", Mock(return_value=200))
    assert service.get_current_price_usd("BTC") == 200


@pytest.mark.parametrize("provider", [pricing.BCBProvider, pricing.SFCProvider, pricing.BanxicoProvider, pricing.BCRAProvider])
def test_unavailable_official_rate_is_not_cached_as_a_real_quote(monkeypatch, provider):
    monkeypatch.setenv("BANXICO_TOKEN", "demo-only")
    monkeypatch.setattr(pricing.requests, "get", Mock(side_effect=TimeoutError("offline")))
    instance = provider()
    assert instance.get_rate(1700000000) == 0
    assert instance._cache_rates == {}
