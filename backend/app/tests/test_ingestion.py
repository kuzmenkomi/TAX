from __future__ import annotations

import zipfile
from pathlib import Path
from uuid import uuid4

import pandas as pd
from app.ingestion.csv_loader import load_csv


def _write_csv(path, content: str) -> str:
    path.write_text(content, encoding='utf-8')
    return str(path)


def _write_zip(path, files: dict[str, str]) -> str:
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return str(path)


def _tmp_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "scratch" / "test_ingestion"
    path = root / f"case-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


NATIVE_CSV = (
    'timestamp,asset,type,amount,fee,from_wallet,to_wallet\n'
    '2026-01-01 00:00:00,BTC,BUY,1.0,0.0,Exchange,Wallet\n'
)

ALIAS_CSV = (
    'date,currency,side,quantity,commission,from_wallet,to_wallet\n'
    '2026-01-01 00:00:00,BTC,BUY,1.0,0.0,Exchange,Wallet\n'
)


def test_load_csv_native():
    tmp_path = _tmp_dir()
    file_path = _write_csv(tmp_path / 'native.csv', NATIVE_CSV)
    df = load_csv(file_path)

    assert len(df) == 1
    assert df.loc[0, 'asset'] == 'BTC'
    assert list(df.columns)[:3] == ['timestamp', 'asset', 'type']


def test_load_csv_native_alias_columns():
    tmp_path = _tmp_dir()
    file_path = _write_csv(tmp_path / 'alias.csv', ALIAS_CSV)
    df = load_csv(file_path)

    assert len(df) == 1
    assert 'timestamp' in df.columns
    assert 'asset' in df.columns
    assert 'type' in df.columns
    assert df.loc[0, 'asset'] == 'BTC'


def test_load_csv_zip_single_file():
    tmp_path = _tmp_dir()
    zip_path = _write_zip(tmp_path / 'archive.zip', {'native.csv': NATIVE_CSV})
    df = load_csv(zip_path)

    assert len(df) == 1
    assert df.loc[0, 'type'] == 'BUY'


def test_load_csv_zip_multiple_files():
    tmp_path = _tmp_dir()
    zip_path = _write_zip(
        tmp_path / 'multi.zip',
        {
            'part1.csv': NATIVE_CSV,
            'part2.csv': NATIVE_CSV.replace('BTC', 'ETH'),
        },
    )
    df = load_csv(zip_path)

    assert len(df) == 2
    assert set(df['asset'].tolist()) == {'BTC', 'ETH'}
