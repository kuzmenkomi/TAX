"""Cloudflare IP Geolocation helpers (CF-IPCountry header)."""

from __future__ import annotations

from fastapi import Request

from app.countries.registries.country_registry import CountryRegistry

# Cloudflare reserved / non-country codes (see Cloudflare docs).
_CF_NON_COUNTRY = frozenset({"XX", "T1", "A1", "A2"})

DEFAULT_JURISDICTION = "BR"


def get_cf_ip_country(request: Request) -> str | None:
    """Read ISO 3166-1 alpha-2 country from Cloudflare (case-insensitive)."""
    raw = request.headers.get("CF-IPCountry") or request.headers.get("cf-ipcountry")
    if not raw:
        return None
    code = raw.strip().upper()
    if not code or code in _CF_NON_COUNTRY:
        return None
    if len(code) != 2 or not code.isalpha():
        return None
    return code


def resolve_jurisdiction(cf_country: str | None) -> tuple[str, str]:
    """
    Map Cloudflare country code to a supported jurisdiction.

    Returns (code, display_name). Falls back to Brazil when unsupported or unknown.
    """
    if cf_country and CountryRegistry.is_supported(cf_country):
        info = CountryRegistry.get_country(cf_country).get_country_info()
        return cf_country, str(info.get("name", cf_country))

    fallback = CountryRegistry.get_country(DEFAULT_JURISDICTION).get_country_info()
    return DEFAULT_JURISDICTION, str(fallback.get("name", "Brazil"))
