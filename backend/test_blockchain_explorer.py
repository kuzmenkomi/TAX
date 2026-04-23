"""
Test blockchain explorer functionality.

Tests transaction fetching from various blockchains using public API keys.
"""

import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.blockchain_explorer import (
    get_explorer,
    fetch_wallet_transactions,
)


def test_ethereum_explorer():
    """Test Ethereum explorer with public address."""
    print("\n" + "="*60)
    print("TEST: Ethereum Explorer")
    print("="*60)
    
    # Vitalik's address (public knowledge, safe for testing)
    address = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    
    try:
        df = fetch_wallet_transactions(address, "ethereum", None)
        print(f"✓ Successfully fetched {len(df)} TX from Ethereum")
        print(f"  Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"  Assets found: {df['asset'].unique().tolist()}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"\nFirst TX:")
            print(df.iloc[0].to_string())
    except Exception as e:
        print(f"✗ Ethereum explorer failed: {e}")


def test_polygon_explorer():
    """Test Polygon explorer."""
    print("\n" + "="*60)
    print("TEST: Polygon Explorer")
    print("="*60)
    
    # Test address (randomly chosen, safe for testing)
    address = "0x742d35Cc6634C0532925a3b844Bc9e7595f44d11"
    
    try:
        df = fetch_wallet_transactions(address, "polygon", None)
        print(f"✓ Successfully fetched {len(df)} TX from Polygon")
        print(f"  Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"  Assets found: {df['asset'].unique().tolist()}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Polygon explorer failed: {e}")


def test_bitcoin_explorer():
    """Test Bitcoin explorer."""
    print("\n" + "="*60)
    print("TEST: Bitcoin Explorer")
    print("="*60)
    
    # Test address (public address with known history)
    address = "1A1z7agoat6Fa59z51gBQRwCR963LoMXB"
    
    try:
        df = fetch_wallet_transactions(address, "bitcoin", None)
        print(f"✓ Successfully fetched {len(df)} TX from Bitcoin")
        print(f"  Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"  Assets found: {df['asset'].unique().tolist()}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Bitcoin explorer failed: {e}")


def test_solana_explorer():
    """Test Solana explorer."""
    print("\n" + "="*60)
    print("TEST: Solana Explorer")
    print("="*60)
    
    # Known Solana address
    address = "So11111111111111111111111111111111111111112"
    
    try:
        df = fetch_wallet_transactions(address, "solana", None)
        print(f"✓ Successfully fetched {len(df)} TX from Solana")
        print(f"  Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"  Assets found: {df['asset'].unique().tolist()}")
    except Exception as e:
        print(f"✗ Solana explorer failed: {e}")


def test_explorer_factory():
    """Test explorer factory function."""
    print("\n" + "="*60)
    print("TEST: Explorer Factory")
    print("="*60)
    
    chains = ["ethereum", "polygon", "bitcoin", "solana", "tron"]
    
    for chain in chains:
        try:
            explorer = get_explorer(chain, None)
            chain_name = explorer.get_chain_name()
            print(f"✓ {chain:12} -> {chain_name}")
        except Exception as e:
            print(f"✗ {chain:12} -> ERROR: {e}")


def test_validated_dataframe_structure():
    """Test that returned DataFrames have correct structure."""
    print("\n" + "="*60)
    print("TEST: DataFrame Structure Validation")
    print("="*60)
    
    required_columns = {
        "timestamp",
        "asset", 
        "type",
        "amount",
        "fee",
        "fee_asset",
        "from_wallet",
        "to_wallet",
        "network",
    }
    
    chains = {
        "ethereum": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "bitcoin": "1A1z7agoat6Fa59z51gBQRwCR963LoMXB",
    }
    
    for chain, address in chains.items():
        try:
            df = fetch_wallet_transactions(address, chain, None)
            if len(df) == 0:
                print(f"⚠ {chain:15} -> No transactions found (data OK, but empty)")
                continue
                
            missing = required_columns - set(df.columns)
            if missing:
                print(f"✗ {chain:15} -> Missing columns: {missing}")
            else:
                print(f"✓ {chain:15} -> All required columns present")
                
                # Validate data types
                for col in ["timestamp", "asset", "type", "amount", "fee", "network"]:
                    if col not in df.columns:
                        continue
                    val = df[col].iloc[0]
                    print(f"    {col:15} -> {type(val).__name__}")
                    
        except Exception as e:
            print(f"✗ {chain:15} -> {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BLOCKCHAIN EXPLORER TEST SUITE")
    print("="*60)
    
    # Run tests
    test_explorer_factory()
    test_ethereum_explorer()
    test_polygon_explorer()
    test_bitcoin_explorer()
    test_solana_explorer()
    test_validated_dataframe_structure()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
