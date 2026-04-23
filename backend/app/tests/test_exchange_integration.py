from __future__ import annotations

import pytest

from app.integrations.exchange_ccxt import fetch_exchange_spot_trades_dataframe


def test_fetch_exchange_spot_trades_dataframe_unsupported_provider() -> None:
    with pytest.raises(RuntimeError, match="Unsupported provider"):
        fetch_exchange_spot_trades_dataframe("unknown_exchange", "key", "secret")
