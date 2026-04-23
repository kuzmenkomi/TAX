from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CountryCapabilities:
    country: str
    label: str
    accounting_methods: tuple[str, ...]


# Minimal MVP mapping.
# Notes:
# - rp2 supports fifo/lifo/hifo for US (and lofo, but we deliberately hide it per request).
# - AVCO is implemented by our internal engine (average cost).
COUNTRIES: tuple[CountryCapabilities, ...] = (
    CountryCapabilities(country="us", label="United States", accounting_methods=("FIFO", "LIFO", "HIFO")),
    CountryCapabilities(country="uk", label="United Kingdom", accounting_methods=("AVCO",)),
    CountryCapabilities(country="de", label="Germany", accounting_methods=("AVCO",)),
    # Initial support for Brazil: practitioners often use average-cost like approaches in practice.
    # For MVP we expose both FIFO and AVCO and will validate with local tax advisors.
    CountryCapabilities(country="br", label="Brazil", accounting_methods=("FIFO", "AVCO")),
)


def list_countries() -> list[dict[str, object]]:
    return [{"country": c.country, "label": c.label, "accounting_methods": list(c.accounting_methods)} for c in COUNTRIES]


def is_method_allowed(country: str, method: str) -> bool:
    country = (country or "").lower().strip()
    method = (method or "").upper().strip()
    for c in COUNTRIES:
        if c.country == country:
            return method in c.accounting_methods
    return False

