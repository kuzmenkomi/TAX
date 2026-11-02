import pandas as pd
from .base import BaseAdapter


class BinanceAdapter(BaseAdapter):
    """
    Supports two Binance CSV layouts:

    Format A - Transaction History:
      UTC_Time | Account | Operation | Asset | Change | Remark

    Format B - Spot Trade / Account export:
      Date(UTC) | Category | Market | Type | Price | Amount | Total | Fee | Fee Coin
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = set(df.columns)
        is_format_b = "Market" in cols or "Date(UTC)" in cols
        if is_format_b:
            return self._transform_format_b(df, cols)
        return self._transform_format_a(df, cols)

    def _ensure_columns(self, cols: set[str], required: set[str], format_name: str) -> None:
        missing = sorted(required - cols)
        if missing:
            raise ValueError(f"Invalid Binance {format_name} CSV. Missing columns: {missing}.")

    def _transform_format_a(self, df: pd.DataFrame, cols: set[str]) -> pd.DataFrame:
        self._ensure_columns(cols, {"Asset", "Change", "Operation"}, "Transaction History")
        out = pd.DataFrame()

        time_col = "UTC_Time" if "UTC_Time" in cols else "Date(UTC)"
        if time_col not in cols:
            raise ValueError("Invalid Binance Transaction History CSV. Missing time column: 'UTC_Time' or 'Date(UTC)'.")
        out["timestamp"] = pd.to_datetime(df[time_col])

        out["asset"] = df["Asset"].astype(str).str.upper()
        out["amount"] = pd.to_numeric(df["Change"], errors="coerce").abs()

        def _map_type(op: str) -> str:
            op = str(op).strip().lower()
            if "deposit" in op:
                return "RECEIVE"
            if "withdraw" in op:
                return "TRANSFER"
            if "buy" in op:
                return "BUY"
            if "sell" in op:
                return "SELL"
            if "staking" in op:
                return "STAKING_REWARD"
            if "reward" in op:
                return "REWARD"
            return "RECEIVE"

        out["type"] = df["Operation"].apply(_map_type)
        out["fee"] = 0.0
        out["price"] = 0.0
        out["from_wallet"] = ""
        out["to_wallet"] = ""
        out["network"] = "binance"
        out["exchange"] = "binance"
        return out

    def _transform_format_b(self, df: pd.DataFrame, cols: set[str]) -> pd.DataFrame:
        self._ensure_columns(cols, {"Date(UTC)", "Market", "Type", "Amount"}, "Spot Trade")
        out = pd.DataFrame()

        out["timestamp"] = pd.to_datetime(df["Date(UTC)"], errors="coerce")
        if out["timestamp"].isna().any():
            raise ValueError("Some Binance timestamps cannot be parsed. Expected 'Date(UTC)' format.")

        pair_col = "Market" if "Market" in cols else "Pair"
        quote_currencies = ["USDT", "BUSD", "USDC", "TUSD", "BNB", "ETH", "BTC"]

        def _extract_base(pair: str) -> str:
            pair = str(pair).strip().upper()
            for quote in quote_currencies:
                if pair.endswith(quote) and len(pair) > len(quote):
                    return pair[:-len(quote)]
            return pair

        out["asset"] = df[pair_col].apply(_extract_base)

        category_col = "Category" if "Category" in cols else None
        side_col = "Type" if "Type" in cols else "Side"

        def _map_type(row: pd.Series) -> str:
            category = str(row.get(category_col, "") if category_col else "").strip().upper()
            side = str(row.get(side_col, "")).strip().upper()

            if category == "TRANSFER":
                if side == "DEPOSIT":
                    return "RECEIVE"
                if side in {"WITHDRAW", "WITHDRAWAL"}:
                    return "TRANSFER"
            if category == "INCOME":
                if side == "AIRDROP":
                    return "AIRDROP"
                if side in {"STAKING", "STAKING_REWARD"}:
                    return "STAKING_REWARD"
                if side in {"REFERRAL", "REWARD"}:
                    return "REWARD"
                return "INCOME"
            if side == "BUY":
                return "BUY"
            if side == "SELL":
                return "SELL"

            raise ValueError(
                f"Unsupported Binance transaction type '{side}'"
                + (f" in category '{category}'" if category else "")
                + "."
            )

        out["type"] = df.apply(_map_type, axis=1)
        out["amount"] = pd.to_numeric(df["Amount" if "Amount" in cols else "Executed"], errors="coerce").abs()
        out["price"] = pd.to_numeric(df["Price"] if "Price" in cols else 0, errors="coerce").fillna(0.0)

        if "Total" in cols:
            out["total_value"] = pd.to_numeric(df["Total"], errors="coerce").abs()
        else:
            out["total_value"] = out["amount"] * out["price"]

        out["fee"] = pd.to_numeric(df["Fee"] if "Fee" in cols else 0, errors="coerce").fillna(0.0)

        fee_coin_col = next((c for c in ("Fee Coin", "FeeCoin", "Fee_Coin") if c in cols), None)
        if fee_coin_col:
            out["fee_asset"] = df[fee_coin_col].astype(str).str.strip().str.upper()
        else:
            out["fee_asset"] = ""

        out["from_wallet"] = ""
        out["to_wallet"] = ""
        out["network"] = "binance"
        out["exchange"] = "binance"
        return out
