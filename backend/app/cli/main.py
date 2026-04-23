from __future__ import annotations

import argparse
import subprocess
import os
import sys

from app.config.settings import load_config
from app.ingestion.csv_loader import load_csv
from app.ingestion.registry import AdapterRegistry
from app.matching.service import match_transfers
from app.normalization.normalizer import normalize, group_swaps
from app.exporters.rp2_ods_exporter import export_to_rp2_ods
from app.accounting.pricing import PriceService
from app.accounting.price_fill import add_synthetic_opening_balances, fill_missing_prices


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crypto Tax Engine CLI")
    parser.add_argument("--config", default=None, help="Path to JSON config")
    parser.add_argument("--file", required=True, help="Input CSV path")
    parser.add_argument("--format", default="native", help="Input format")
    parser.add_argument(
        "--method",
        default=None,
        choices=["fifo", "lifo", "hifo", "lofo"],
        help="Accounting method for RP2 (fifo/lifo/hifo/lofo). If omitted, uses config/default.",
    )
    return parser


def map_transaction_type(tx: str) -> str:
    tx = str(tx).lower()

    mapping = {
        "buy": "IN",
        "sell": "OUT",
        "transfer": "TRANSFER",
        "receive": "IN",
        "deposit": "IN",
        "withdraw": "OUT",
        "swap": "TRADE"
    }

    return mapping.get(tx, "TRANSFER").upper()


def run_cli() -> None:
    # Some Windows consoles default to a legacy encoding (e.g. cp1251) which can't print emoji.
    # Avoid non-ascii output to prevent UnicodeEncodeError.
    print("\n--- CRYPTO TAX ENGINE (POWERED BY RP2) ---")

    try:
        args = build_parser().parse_args()
        cfg = load_config(args.config)

        raw = load_csv(args.file, validate_native_schema=(args.format == "native"))

        if args.format != "native":
            raw = AdapterRegistry.get_adapter(args.format).transform(raw)

        print("Loaded rows:", len(raw))

        print("Step 1: Exporting to RP2 format...")

        normalized = normalize(raw)

        # normalize transaction types for RP2
        normalized["type"] = normalized["type"].apply(map_transaction_type)

        normalized = group_swaps(normalized)

        # Ensure spot prices exist where needed (RP2 requires spot_price > 0 for IN rows).
        price_service = PriceService()
        normalized = fill_missing_prices(normalized, price_service)
        normalized = add_synthetic_opening_balances(normalized, price_service)

        matches = match_transfers(normalized, cfg.matching)

        paths = export_to_rp2_ods(
            normalized,
            matches,
            cfg.reporting.output_dir
        )

        print("Step 2: Running RP2 Engine...")

        scripts_path = os.path.join(os.path.dirname(sys.executable), "Scripts")
        rp2_exe = os.path.join(scripts_path, "rp2_us.exe")

        if not os.path.exists(rp2_exe):
            rp2_exe = "rp2_us"

        output_path = os.path.join(cfg.reporting.output_dir, "rp2_reports")

        method = (args.method or cfg.tax.accounting_method or "fifo").lower()
        cmd = [
            rp2_exe,
            "-o", output_path,
            "-p", "tax_",
            "-n",
            "-m", method,
            paths["ini"],
            paths["ods"]
        ]

        result = subprocess.run(cmd, text=True)

        if result.returncode == 0:
            print("\n=== SUCCESS ===")
            print(f"Reports saved to: {output_path}")
        else:
            print(f"\nRP2 error (code {result.returncode})")

    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_cli()