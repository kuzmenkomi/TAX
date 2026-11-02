from __future__ import annotations

from pathlib import Path

import ezodf
import pandas as pd


def export_to_rp2_ods(df: pd.DataFrame, matches, output_dir: str = "output") -> dict[str, str]:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ods_file = out_path / "rp2_input.ods"

    def _iso_utc(value) -> str:
        ts = pd.Timestamp(value)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        return ts.isoformat()

    def _spot_price(row: pd.Series) -> float:
        try:
            v = float(row.get("price", 0.0) or 0.0)
            if pd.isna(v) or v < 0:
                v = 0.0
        except Exception:
            v = 0.0

        # RP2 requires spot_price > 0 for IN transactions. If it's missing, try to derive
        # it from total_value / amount (normalizer often does this, but keep a fallback here).
        if v == 0.0:
            try:
                total_value = row.get("total_value", None)
                amount = float(row.get("amount", 0.0) or 0.0)
                if total_value is not None and not pd.isna(total_value) and amount != 0.0:
                    derived = float(total_value) / amount
                    if not pd.isna(derived) and derived > 0.0:
                        v = derived
            except Exception:
                pass

        return float(v)

    def _fiat_value(amount: float, spot_price: float, fallback) -> float:
        try:
            if fallback is not None:
                fv = float(fallback)
                if not pd.isna(fv) and fv != 0.0:
                    return fv
        except Exception:
            pass
        return float(amount) * float(spot_price)

    def _fiat_fee(row: pd.Series, spot_price: float) -> float:
        try:
            fee = float(row.get("fee", 0.0) or 0.0)
        except Exception:
            fee = 0.0
        return fee * float(spot_price)

    def _map_in_type(tx_type: str) -> str:
        t = str(tx_type).upper()
        if t in ("INTEREST", "EARN", "STAKING"):
            return "INTEREST"
        return "BUY"

    def _clean_uid(val, default_val: str) -> str:
        if val is None or pd.isna(val) or val == "":
            return default_val
        return str(val)

    # RP2 requires a non-empty IN table for each configured asset:
    in_assets_set: set[str] = set()
    if "asset" in df.columns:
        mask_in = df["type"].isin(["BUY", "IN", "RECEIVE", "INTEREST"])
        in_assets_set |= set(df.loc[mask_in, "asset"].dropna().astype(str).str.upper().unique())
    if "asset_in" in df.columns:
        mask_swap_in = df["type"].isin(["SWAP", "TRADE"])
        in_assets_set |= set(df.loc[mask_swap_in, "asset_in"].dropna().astype(str).str.upper().unique())
    in_assets_set.discard("SWAP")
    in_assets_set.discard("")
    assets = sorted(in_assets_set)

    doc = ezodf.newdoc("ods", str(ods_file))

    for asset in assets:
        rows: list[list[object]] = []

        rows.append(["IN"])
        rows.append(
            [
                "Timestamp",
                "Exchange",
                "Holder",
                "Transaction Type",
                "Asset",
                "Crypto In",
                "Spot Price",
                "Crypto Fee",
                "Fiat In (No Fee)",
                "Fiat In (With Fee)",
                "Fiat Fee",
                "Unique Id",
                "Notes",
            ]
        )

        for idx, r in df[df["type"].isin(["BUY", "IN", "RECEIVE", "DEPOSIT", "INTEREST"]) & (df["asset"] == asset)].iterrows():
            spot_price = _spot_price(r)
            crypto_in = float(r.get("amount", 0.0) or 0.0)
            crypto_fee = float(r.get("fee", 0.0) or 0.0)
            fiat_in_no_fee = _fiat_value(crypto_in, spot_price, r.get("total_value"))
            # RP2 input must define either crypto_fee or fiat_fee (not both). We pass crypto_fee
            # and let RP2 infer fiat_fee via spot_price.
            fiat_in_with_fee = fiat_in_no_fee + (crypto_fee * spot_price)
            rows.append(
                [
                    _iso_utc(r["timestamp"]),
                    r.get("to_wallet") or r.get("from_wallet") or "Unknown",
                    "Owner",
                    _map_in_type(r.get("type", "")),
                    asset,
                    crypto_in,
                    float(spot_price),
                    float(crypto_fee),
                    float(fiat_in_no_fee),
                    float(fiat_in_with_fee),
                    None,
                    _clean_uid(r.get("external_id"), f"row_{idx}"),
                    "",
                ]
            )

        if "asset_in" in df.columns:
            for idx, r in df[df["type"].isin(["SWAP", "TRADE"]) & (df["asset_in"] == asset)].iterrows():
                amount_in = float(r.get("amount_in", 0.0) or 0.0)
                if amount_in <= 0:
                    continue
                fiat_in_no_fee = _fiat_value(amount_in, 0.0, r.get("total_value"))
                uid = _clean_uid(r.get("external_id"), f"row_{idx}") + "_in"
                rows.append(
                    [
                        _iso_utc(r["timestamp"]),
                        r.get("to_wallet") or r.get("from_wallet") or "Unknown",
                        "Owner",
                        "BUY",
                        asset,
                        amount_in,
                        0.0,
                        0.0,
                        float(fiat_in_no_fee),
                        float(fiat_in_no_fee),
                        None,
                        uid,
                        f"SWAP in leg: {r.get('asset_out','')} -> {asset}",
                    ]
                )

        rows.append(["TABLE END"])

        rows.append(["OUT"])
        rows.append(
            [
                "Timestamp",
                "Exchange",
                "Holder",
                "Transaction Type",
                "Asset",
                "Crypto Out",
                "Spot Price",
                "Crypto Fee",
                "Crypto Out (With Fee)",
                "Fiat Out (No Fee)",
                "Fiat Fee",
                "Unique Id",
                "Notes",
            ]
        )

        for idx, r in df[df["type"].isin(["SELL", "OUT", "WITHDRAW"]) & (df["asset"] == asset)].iterrows():
            spot_price = _spot_price(r)
            crypto_out_no_fee = float(r.get("amount", 0.0) or 0.0)
            crypto_fee = float(r.get("fee", 0.0) or 0.0)
            crypto_out_with_fee = crypto_out_no_fee + crypto_fee
            fiat_out_no_fee = _fiat_value(crypto_out_no_fee, spot_price, r.get("total_value"))
            rows.append(
                [
                    _iso_utc(r["timestamp"]),
                    r.get("from_wallet") or "Unknown",
                    "Owner",
                    "SELL",
                    asset,
                    crypto_out_no_fee,
                    float(spot_price),
                    float(crypto_fee),
                    float(crypto_out_with_fee),
                    float(fiat_out_no_fee),
                    None,
                    _clean_uid(r.get("external_id"), f"row_{idx}"),
                    "",
                ]
            )

        if "asset_out" in df.columns:
            for idx, r in df[df["type"].isin(["SWAP", "TRADE"]) & (df["asset_out"] == asset)].iterrows():
                amount_out = float(r.get("amount_out", 0.0) or 0.0)
                if amount_out <= 0:
                    continue
                spot_price = _spot_price(r)
                crypto_fee = float(r.get("fee", 0.0) or 0.0)
                crypto_out_with_fee = amount_out + crypto_fee
                fiat_out_no_fee = _fiat_value(amount_out, spot_price, r.get("total_value"))
                uid = _clean_uid(r.get("external_id"), f"row_{idx}") + "_out"
                rows.append(
                    [
                        _iso_utc(r["timestamp"]),
                        r.get("from_wallet") or "Unknown",
                        "Owner",
                        "SELL",
                        asset,
                        amount_out,
                        float(spot_price),
                        float(crypto_fee),
                        float(crypto_out_with_fee),
                        float(fiat_out_no_fee),
                        None,
                        uid,
                        f"SWAP out leg: {asset} -> {r.get('asset_in','')}",
                    ]
                )

        rows.append(["TABLE END"])

        rows.append(["INTRA"])
        rows.append(
            [
                "Timestamp",
                "From Exchange",
                "From Holder",
                "To Exchange",
                "To Holder",
                "Asset",
                "Spot Price",
                "Crypto Sent",
                "Crypto Received",
                "Unique Id",
                "Notes",
            ]
        )

        for idx, r in df[df["type"].isin(["TRANSFER"]) & (df["asset"] == asset)].iterrows():
            spot_price = _spot_price(r)
            crypto_sent = float(r.get("amount", 0.0) or 0.0)
            crypto_fee = float(r.get("fee", 0.0) or 0.0)
            crypto_received = crypto_sent - crypto_fee
            rows.append(
                [
                    _iso_utc(r["timestamp"]),
                    r.get("from_wallet") or "Unknown",
                    "Owner",
                    r.get("to_wallet") or "Unknown",
                    "Owner",
                    asset,
                    float(spot_price),
                    crypto_sent,
                    crypto_received,
                    _clean_uid(r.get("external_id"), f"row_{idx}"),
                    "",
                ]
            )

        rows.append(["TABLE END"])

        table = ezodf.Table(asset)
        doc.sheets += table
        max_cols = max(len(r) for r in rows) if rows else 1
        table.reset(size=(len(rows), max_cols))
        for r_i, row in enumerate(rows):
            for c_i, value in enumerate(row):
                if value is None:
                    continue
                table[r_i, c_i].set_value(value)

    doc.save()

    # =========================
    # RP2 CONFIG (FIXED)
    # =========================

    assets_csv = ",".join(assets)
    exchanges = ",".join(sorted(
        set(df["from_wallet"].dropna().unique()) |
        set(df["to_wallet"].dropna().unique())
    ))

    ini_file = out_path / "rp2_config.ini"

    ini_content = f"""[general]
accounting_method = fifo
country = us
assets = {assets_csv}
exchanges = {exchanges}
holders = Owner

[in_header]
timestamp = 0
exchange = 1
holder = 2
transaction_type = 3
asset = 4
crypto_in = 5
spot_price = 6
crypto_fee = 7
fiat_in_no_fee = 8
fiat_in_with_fee = 9
fiat_fee = 10
unique_id = 11
notes = 12

[out_header]
timestamp = 0
exchange = 1
holder = 2
transaction_type = 3
asset = 4
crypto_out_no_fee = 5
spot_price = 6
crypto_fee = 7
crypto_out_with_fee = 8
fiat_out_no_fee = 9
fiat_fee = 10
unique_id = 11
notes = 12

[intra_header]
timestamp = 0
from_exchange = 1
from_holder = 2
to_exchange = 3
to_holder = 4
asset = 5
spot_price = 6
crypto_sent = 7
crypto_received = 8
unique_id = 9
notes = 10
"""

    ini_file.write_text(ini_content, encoding="utf-8")

    return {"ods": str(ods_file), "ini": str(ini_file)}