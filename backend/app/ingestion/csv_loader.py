from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from app.normalization.normalizer import apply_column_aliases, validate_required_columns


def _read_csv_file(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith('.zip'):
        return _read_csv_from_zip(file_path)
    return pd.read_csv(file_path)


def _read_csv_from_zip(file_path: str) -> pd.DataFrame:
    with zipfile.ZipFile(file_path, 'r') as zf:
        csv_names = [name for name in zf.namelist() if not name.endswith('/') and Path(name).suffix.lower() in {'.csv', '.txt'}]
        if not csv_names:
            raise ValueError('ZIP archive does not contain CSV files.')

        frames: list[pd.DataFrame] = []
        for name in csv_names:
            with zf.open(name) as handle:
                data = handle.read()
                frames.append(pd.read_csv(io.BytesIO(data)))

        if not frames:
            raise ValueError('ZIP archive does not contain readable CSV files.')

        return pd.concat(frames, ignore_index=True)


def load_raw_csv(file_path: str) -> pd.DataFrame:
    """Load CSV or ZIP without enforcing the project's native schema."""
    df = _read_csv_file(file_path)
    print(f"Loaded rows: {len(df)}")
    return df


def load_csv(file_path: str, *, validate_native_schema: bool = True) -> pd.DataFrame:
    """
    Load CSV or ZIP and optionally validate it matches the project's native schema.

    For exchange-specific formats (binance/bybit/coinbase) pass validate_native_schema=False,
    then transform via an adapter, then run normalizer.normalize().
    """
    df = _read_csv_file(file_path)
    df = apply_column_aliases(df)
    if validate_native_schema:
        validate_required_columns(df.columns)
    print(f"Loaded rows: {len(df)}")
    return df
