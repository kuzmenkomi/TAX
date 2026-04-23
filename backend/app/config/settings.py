from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MatchingConfig:
    max_amount_diff: float
    max_time_diff_seconds: int


@dataclass(frozen=True)
class TaxConfig:
    accounting_method: str
    base_currency: str


@dataclass(frozen=True)
class ReportingConfig:
    output_dir: str
    write_json: bool
    write_csv: bool
    write_summary: bool


@dataclass(frozen=True)
class AppConfig:
    matching: MatchingConfig
    tax: TaxConfig
    reporting: ReportingConfig


def load_config(config_path: str | None = None) -> AppConfig:
    default_path = Path(__file__).with_name("default.json")
    path = Path(config_path) if config_path else default_path
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    return AppConfig(
        matching=MatchingConfig(
            max_amount_diff=float(raw["matching"]["max_amount_diff"]),
            max_time_diff_seconds=int(raw["matching"]["max_time_diff_seconds"]),
        ),
        tax=TaxConfig(
            accounting_method=str(raw["tax"]["accounting_method"]),
            base_currency=str(raw["tax"]["base_currency"]),
        ),
        reporting=ReportingConfig(
            output_dir=str(raw["reporting"]["output_dir"]),
            write_json=bool(raw["reporting"]["write_json"]),
            write_csv=bool(raw["reporting"]["write_csv"]),
            write_summary=bool(raw["reporting"]["write_summary"]),
        ),
    )
