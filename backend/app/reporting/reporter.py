from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class RunMetadata:
    run_id: str
    generated_at_utc: str
    input_file: str
    input_hash_sha256: str


def build_metadata(input_file: str) -> RunMetadata:
    file_hash = hashlib.sha256(Path(input_file).read_bytes()).hexdigest()
    return RunMetadata(
        run_id=str(uuid.uuid4()),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        input_file=input_file,
        input_hash_sha256=file_hash,
    )


def write_reports(
    output_dir: str,
    metadata: RunMetadata,
    pnl: dict[str, Any],
    matches: list[dict[str, Any]],
    normalized_df: pd.DataFrame,
    write_json: bool = True,
    write_csv: bool = True,
    write_summary: bool = True,
) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    created: dict[str, str] = {}

    report_payload = {
        "metadata": asdict(metadata),
        "summary": {
            # ИСПРАВЛЕНО: правильный ключ total_realized_pnl_usd (было total_realized_pnl)
            "total_pnl_usd": pnl.get("total_realized_pnl_usd", 0.0),
            "by_asset": pnl.get("realized_pnl_by_asset", {}),
            "trades": int(len(normalized_df)),
            "matches": int(len(matches)),
            # ИСПРАВЛЕНО: правильный ключ taxable_events_count (было taxable_sell_count)
            "taxable_events_count": int(pnl.get("taxable_events_count", 0)),
            "internal_transfer_count": int(pnl.get("internal_transfer_count", 0)),
            "total_gas_fees_usd": float(pnl.get("total_gas_fees_usd", 0.0)),
        },
    }

    if write_json:
        json_file = out / "report.json"
        json_file.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        created["json"] = str(json_file)

    if write_csv:
        summary_csv = out / "report_summary.csv"
        pd.DataFrame(
            [{"metric": k, "value": v} for k, v in report_payload["summary"].items()
             if not isinstance(v, dict)]
        ).to_csv(summary_csv, index=False)
        created["summary_csv"] = str(summary_csv)

        matches_csv = out / "report_matches.csv"
        pd.DataFrame(matches).to_csv(matches_csv, index=False)
        created["matches_csv"] = str(matches_csv)

        # ДОБАВЛЕНО: отдельный CSV по P&L активов
        assets_csv = out / "report_by_asset.csv"
        pd.DataFrame(
            [{"asset": k, "pnl_usd": v} for k, v in pnl.get("realized_pnl_by_asset", {}).items()]
        ).to_csv(assets_csv, index=False)
        created["assets_csv"] = str(assets_csv)

    if write_summary:
        summary_file = out / "report_summary.txt"
        lines = [
            f"run_id: {metadata.run_id}",
            f"generated_at_utc: {metadata.generated_at_utc}",
            f"input_hash_sha256: {metadata.input_hash_sha256}",
            f"total_pnl_usd: {report_payload['summary']['total_pnl_usd']}",
            f"trades: {report_payload['summary']['trades']}",
            f"matches: {report_payload['summary']['matches']}",
            f"taxable_events_count: {report_payload['summary']['taxable_events_count']}",
            f"internal_transfer_count: {report_payload['summary']['internal_transfer_count']}",
            f"total_gas_fees_usd: {report_payload['summary']['total_gas_fees_usd']}",
        ]
        summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        created["summary_txt"] = str(summary_file)

    return created