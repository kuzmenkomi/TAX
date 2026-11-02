"""Tests for Cloudflare CF-IPCountry geo resolution."""

from unittest.mock import MagicMock

import pytest

from app.core.cloudflare_geo import (
    DEFAULT_JURISDICTION,
    get_cf_ip_country,
    resolve_jurisdiction,
)
from app.countries import CountryRegistry  # noqa: F401 — registers countries


def _request(headers: dict[str, str]) -> MagicMock:
    req = MagicMock()
    req.headers = headers
    return req


class TestGetCfIpCountry:
    def test_reads_cf_ipcountry_header(self):
        assert get_cf_ip_country(_request({"CF-IPCountry": "br"})) == "BR"

    def test_lowercase_header(self):
        assert get_cf_ip_country(_request({"cf-ipcountry": "us"})) == "US"

    def test_ignores_unknown_codes(self):
        assert get_cf_ip_country(_request({"CF-IPCountry": "XX"})) is None
        assert get_cf_ip_country(_request({"CF-IPCountry": "T1"})) is None

    def test_missing_header(self):
        assert get_cf_ip_country(_request({})) is None


class TestResolveJurisdiction:
    def test_brazil(self):
        code, name = resolve_jurisdiction("BR")
        assert code == "BR"
        assert name == "Brazil"

    def test_united_states(self):
        code, name = resolve_jurisdiction("US")
        assert code == "US"
        assert name == "United States"

    def test_unsupported_falls_back(self):
        code, name = resolve_jurisdiction("DE")
        assert code == DEFAULT_JURISDICTION
        assert name == "Brazil"

    def test_none_falls_back(self):
        code, _ = resolve_jurisdiction(None)
        assert code == DEFAULT_JURISDICTION
