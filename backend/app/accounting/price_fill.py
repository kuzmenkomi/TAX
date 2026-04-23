from __future__ import annotations

from typing import Any

import pandas as pd

from app.accounting.pricing import PriceService


_STABLES: set[str] = {"USD", "USDT", "USDC", "BUSD", "DAI", "PYUSD"}


def _ts_to_seconds(value: Any) -> int:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp())


def fill_missing_prices(df: pd.DataFrame, price_service: PriceService) -> pd.DataFrame:
    """
    Ensure RP2-required spot prices exist.

    RP2 requires spot_price > 0 for IN transactions. Many real CSVs don't include price/total_value
    for deposits/receives, so we fetch historical prices and also backfill total_value.
    """

    out = df.copy()
    if "price" not in out.columns:
        out["price"] = pd.NA
    if "total_value" not in out.columns:
        out["total_value"] = pd.NA
    if "price_source" not in out.columns:
        out["price_source"] = pd.NA

    for idx, row in out.iterrows():
        tx_type = str(row.get("type", "")).upper()

        # Determine which asset's spot price is needed for this row.
        asset = str(row.get("asset", "") or "").upper()
        if tx_type in {"SWAP", "TRADE"}:
            asset = str(row.get("asset_out", asset) or "").upper()

        if not asset or asset == "SWAP":
            continue

        price = row.get("price", pd.NA)
        has_price = price is not pd.NA and not pd.isna(price) and float(price) > 0.0
        if not has_price:
            if asset in _STABLES:
                resolved, source = price_service.get_spot_price_with_source(asset, _ts_to_seconds(row.get("timestamp")))
                if resolved <= 0.0:
                    resolved, source = 1.0, "Stablecoin Default"
            else:
                resolved, source = price_service.get_spot_price_with_source(asset, _ts_to_seconds(row.get("timestamp")))
            
            if resolved and resolved > 0.0:
                out.at[idx, "price"] = resolved
                out.at[idx, "price_source"] = source

        # Backfill total_value if missing and amount is available.
        total_value = row.get("total_value", pd.NA)
        if total_value is pd.NA or pd.isna(total_value) or float(total_value) == 0.0:
            amount_field = "amount"
            if tx_type in {"SWAP", "TRADE"}:
                amount_field = "amount_out"
            amount = row.get(amount_field, pd.NA)
            try:
                amount_f = float(amount)
            except Exception:
                amount_f = 0.0
            try:
                price_f = float(out.at[idx, "price"])
            except Exception:
                price_f = 0.0
            if amount_f and price_f:
                out.at[idx, "total_value"] = amount_f * price_f

    return out


def add_synthetic_opening_balances(df: pd.DataFrame, price_service: PriceService) -> pd.DataFrame:
    """
    Add synthetic opening BUY rows when dataset is incomplete.

    RP2 will abort if total acquired crypto is less than total taxable crypto (sells + fees).
    For a "best-effort" run, inject an opening balance at the earliest timestamp for each
    asset that would otherwise fail.
    """

    out = df.copy()
    if out.empty:
        return out

    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    earliest = out["timestamp"].min()
    if pd.isna(earliest):
        return out

    rows: list[dict[str, Any]] = []

    def _sum(mask) -> float:
        try:
            return float(out.loc[mask, "amount"].astype(float).sum())
        except Exception:
            return 0.0

    assets = set(out.get("asset", pd.Series([], dtype=str)).dropna().astype(str).str.upper().unique())
    if "asset_out" in out.columns:
        assets |= set(out["asset_out"].dropna().astype(str).str.upper().unique())
    if "asset_in" in out.columns:
        assets |= set(out["asset_in"].dropna().astype(str).str.upper().unique())
    assets.discard("SWAP")
    assets.discard("")

    for asset in sorted(assets):
        in_mask = out["type"].isin(["BUY", "IN", "RECEIVE", "DEPOSIT", "INTEREST"]) & (out["asset"].astype(str).str.upper() == asset)
        in_qty = float(out.loc[in_mask, "amount"].astype(float).sum()) if in_mask.any() else 0.0

        out_mask = out["type"].isin(["SELL", "OUT", "WITHDRAW"]) & (out["asset"].astype(str).str.upper() == asset)
        out_qty = float(out.loc[out_mask, "amount"].astype(float).sum()) if out_mask.any() else 0.0

        swap_out_qty = 0.0
        if "asset_out" in out.columns and "amount_out" in out.columns:
            m = out["type"].isin(["SWAP", "TRADE"]) & (out["asset_out"].astype(str).str.upper() == asset)
            if m.any():
                swap_out_qty = float(out.loc[m, "amount_out"].astype(float).sum())

        transfer_fee_qty = 0.0
        if "fee" in out.columns:
            m = out["type"].isin(["TRANSFER"]) & (out["asset"].astype(str).str.upper() == asset)
            if m.any():
                transfer_fee_qty = float(out.loc[m, "fee"].astype(float).sum())

        # Approximate taxable crypto that must be covered by acquired lots.
        required = out_qty + swap_out_qty + transfer_fee_qty
        missing = required - in_qty

        # Also handle ordering: taxable events may occur before the first acquisition row.
        first_in_ts = None
        if in_mask.any():
            first_in_ts = pd.Timestamp(out.loc[in_mask, "timestamp"].min())
        taxable_mask = (
            (out["type"].isin(["SELL", "OUT", "WITHDRAW"]) & (out["asset"].astype(str).str.upper() == asset))
            | (
                out["type"].isin(["TRANSFER"])
                & (out["asset"].astype(str).str.upper() == asset)
                & (out.get("fee", 0.0).astype(float) > 0.0)
            )
        )
        first_taxable_ts = None
        if taxable_mask.any():
            first_taxable_ts = pd.Timestamp(out.loc[taxable_mask, "timestamp"].min())

        # Amount needed to cover taxable events that happen before the first IN lot.
        pre_in_required = 0.0
        if first_in_ts is not None and first_taxable_ts is not None and first_taxable_ts < first_in_ts:
            pre_transfer_fee = 0.0
            m = (
                out["type"].isin(["TRANSFER"])
                & (out["asset"].astype(str).str.upper() == asset)
                & (out["timestamp"] < first_in_ts)
            )
            if m.any():
                try:
                    pre_transfer_fee = float(out.loc[m, "fee"].astype(float).sum())
                except Exception:
                    pre_transfer_fee = 0.0
            pre_sell = 0.0
            m = (
                out["type"].isin(["SELL", "OUT", "WITHDRAW"])
                & (out["asset"].astype(str).str.upper() == asset)
                & (out["timestamp"] < first_in_ts)
            )
            if m.any():
                try:
                    pre_sell = float(out.loc[m, "amount"].astype(float).sum())
                except Exception:
                    pre_sell = 0.0
            pre_in_required = pre_sell + pre_transfer_fee

        needed = max(missing, pre_in_required)
        if needed > 1e-12:
            base_ts = first_taxable_ts if first_taxable_ts is not None else earliest
            ts = pd.Timestamp(base_ts) - pd.Timedelta(seconds=1)
            price, source = (1.0, "Stablecoin Default") if asset in _STABLES else price_service.get_spot_price_with_source(asset, _ts_to_seconds(ts))
            if not price or price <= 0.0:
                price, source = 1.0, "Balance Fallback"
            rows.append(
                {
                    "timestamp": ts,
                    "asset": asset,
                    "type": "BUY",
                    "amount": float(needed),
                    "fee": 0.0,
                    "from_wallet": "OpeningBalance",
                    "to_wallet": "OpeningBalance",
                    "price": float(price),
                    "total_value": float(needed) * float(price),
                    "price_source": source,
                    "external_id": f"synthetic_opening_{asset}",
                }
            )

    if not rows:
        return out

    out2 = pd.concat([pd.DataFrame(rows), out], ignore_index=True)
    out2 = out2.sort_values("timestamp").reset_index(drop=True)
    return out2

