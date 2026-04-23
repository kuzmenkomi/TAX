"""
Exchange integration via CCXT (Cryptocurrency Exchange Trading Library).

Supports 100+ exchanges:
- Tier 1: Binance, Coinbase, Kraken, OKX
- Tier 2: KuCoin, Huobi, Gate.io, Bybit, Crypto.com
- Tier 3: Bitfinex, Poloniex, Kucoin, Upbit, Bithumb
- And 90+ more...

Returns normalized transaction DataFrame compatible with tax pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
import time

import pandas as pd
import ccxt

logger = logging.getLogger(__name__)


class ExchangeAdapter:
    """Abstract base for exchange adapters."""
    
    def __init__(self, exchange_name: str, api_key: str, api_secret: str, passphrase: str | None = None, is_oauth: bool = False):
        """
        Initialize exchange connection.
        
        Args:
            exchange_name: Exchange ID (e.g., 'binance', 'coinbase', 'okx')
            api_key: Exchange API key (or access_token if is_oauth is True)
            api_secret: Exchange API secret (or refresh_token if is_oauth is True)
            passphrase: Exchange passphrase (required for some exchanges like OKX)
            is_oauth: Whether the credentials are OAuth tokens
        """
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.is_oauth = is_oauth
        
        # Initialize CCXT exchange
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            params = {
                'enableRateLimit': True,
            }
            
            if is_oauth:
                params['accessToken'] = api_key
                # Note: secret/password are usually not needed for OAuth in CCXT 
                # but some implementations might use them for refreshing.
            else:
                params['apiKey'] = api_key
                params['secret'] = api_secret
                params['password'] = passphrase  # For OKX and similar
                
            self.exchange = exchange_class(params)
        except AttributeError:
            raise ValueError(f"Exchange '{exchange_name}' not supported by CCXT")
    
    def get_trades(self, symbol: str | None = None, since: datetime | None = None) -> pd.DataFrame:
        """
        Fetch all trades (buys/sells) from exchange.
        
        Args:
            symbol: Optional symbol filter (e.g., 'BTC/USDT')
            since: Optional datetime to fetch trades since
            
        Returns:
            DataFrame with columns: timestamp, asset, type, amount, price, fee, fee_asset, exchange
        """
        try:
            trades_list = []
            
            # Get trading pairs
            symbols = [symbol] if symbol else self.exchange.symbols[:50]  # Limit to first 50 pairs
            
            for sym in symbols:
                for retry in range(3):
                    try:
                        # Fetch trades with rate limiting and incremental support
                        since_ms = int(since.timestamp() * 1000) if since else None
                        trades = self.exchange.fetch_my_trades(symbol=sym, since=since_ms)
                        trades_list.extend(trades)
                        break # Success
                    except ccxt.RateLimitExceeded:
                        wait_time = (2 ** retry) * (self.exchange.rateLimit / 1000)
                        logger.warning(f"Rate limit hit for {sym}, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    except (ccxt.ExchangeError, ccxt.NetworkError) as e:
                        logger.warning(f"Failed to fetch trades for {sym} (retry {retry}): {e}")
                        time.sleep(1)
                        continue
                
                # Rate limit protection (base)
                if self.exchange.has['fetchMyTrades']:
                    time.sleep(self.exchange.rateLimit / 1000)
            
            if not trades_list:
                return pd.DataFrame(columns=self._get_columns())
            
            # Normalize trades
            df = pd.DataFrame(trades_list)
            df = self._normalize_trades(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch trades from {self.exchange_name}: {e}")
            return pd.DataFrame(columns=self._get_columns())
    
            since_ms = int(since.timestamp() * 1000) if since else None
            deposits = self.exchange.fetch_deposits(since=since_ms)
            
            if not deposits:
                return pd.DataFrame(columns=self._get_columns())
            
            df = pd.DataFrame(deposits)
            df = self._normalize_deposits(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch deposits from {self.exchange_name}: {e}")
            return pd.DataFrame(columns=self._get_columns())
    
            since_ms = int(since.timestamp() * 1000) if since else None
            withdrawals = self.exchange.fetch_withdrawals(since=since_ms)
            
            if not withdrawals:
                return pd.DataFrame(columns=self._get_columns())
            
            df = pd.DataFrame(withdrawals)
            df = self._normalize_withdrawals(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch withdrawals from {self.exchange_name}: {e}")
            return pd.DataFrame(columns=self._get_columns())
    
    def get_balance(self) -> dict[str, dict[str, float]]:
        """Get current account balance (free, used, total)."""
        try:
            balance = self.exchange.fetch_balance()
            
            return {
                asset: {
                    'free': balance.get(asset, {}).get('free', 0),
                    'used': balance.get(asset, {}).get('used', 0),
                    'total': balance.get(asset, {}).get('total', 0),
                }
                for asset in balance.keys()
                if asset not in ('free', 'used', 'total')
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch balance from {self.exchange_name}: {e}")
            return {}
    
    def _get_columns(self) -> list[str]:
        """Get list of output columns."""
        return [
            'timestamp',
            'asset',
            'type',  # buy, sell, deposit, withdrawal
            'amount',
            'price',
            'fee',
            'fee_asset',
            'exchange',
            'external_id',  # trade ID or txhash
        ]
    
    def _normalize_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize trade data to standard format."""
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['exchange'] = self.exchange_name
        df['type'] = df['side']  # 'buy' or 'sell'
        df['asset'] = df['symbol'].str.split('/').str[0]  # 'BTC/USDT' -> 'BTC'
        df['amount'] = df['amount']
        df['price'] = df['price']
        df['fee'] = df.get('fee', {}).apply(lambda x: x.get('cost', 0) if isinstance(x, dict) else 0)
        df['fee_asset'] = df.get('fee', {}).apply(lambda x: x.get('currency', '') if isinstance(x, dict) else '')
        df['external_id'] = df['id']
        
        return df[[
            'timestamp', 'asset', 'type', 'amount', 'price', 'fee', 'fee_asset', 'exchange', 'external_id'
        ]]
    
    def _normalize_deposits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize deposit data."""
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['type'] = 'deposit'
        df['asset'] = df['currency']
        df['amount'] = df['amount']
        df['price'] = 0  # Deposits don't have price
        df['fee'] = df.get('fee', {}).apply(lambda x: x.get('cost', 0) if isinstance(x, dict) else 0)
        df['fee_asset'] = df['currency']
        df['exchange'] = self.exchange_name
        df['external_id'] = df['txid']
        
        return df[[
            'timestamp', 'asset', 'type', 'amount', 'price', 'fee', 'fee_asset', 'exchange', 'external_id'
        ]]
    
    def _normalize_withdrawals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize withdrawal data."""
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['type'] = 'withdrawal'
        df['asset'] = df['currency']
        df['amount'] = df['amount']
        df['price'] = 0  # Withdrawals don't have price
        df['fee'] = df.get('fee', {}).apply(lambda x: x.get('cost', 0) if isinstance(x, dict) else 0)
        df['fee_asset'] = df['currency']
        df['exchange'] = self.exchange_name
        df['external_id'] = df['txid']
        
        return df[[
            'timestamp', 'asset', 'type', 'amount', 'price', 'fee', 'fee_asset', 'exchange', 'external_id'
        ]]


def get_exchange_adapter(exchange_name: str, api_key: str, api_secret: str, passphrase: str | None = None, is_oauth: bool = False) -> ExchangeAdapter:
    """Factory function to create exchange adapter."""
    return ExchangeAdapter(exchange_name, api_key, api_secret, passphrase, is_oauth)


def fetch_exchange_transactions(
    exchange_name: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None = None,
    is_oauth: bool = False,
    since: datetime | None = None,
) -> pd.DataFrame:
    """
    Fetch incremental transactions from exchange (trades, deposits, withdrawals).
    """
    try:
        adapter = get_exchange_adapter(exchange_name, api_key, api_secret, passphrase, is_oauth)
        
        # Fetch all transaction types incrementally
        trades = adapter.get_trades(since=since)
        deposits = adapter.get_deposits(since=since)
        withdrawals = adapter.get_withdrawals(since=since)
        
        # Combine all
        all_txs = pd.concat([trades, deposits, withdrawals], ignore_index=True)
        
        # Sort by timestamp
        all_txs['timestamp'] = pd.to_datetime(all_txs['timestamp'], utc=True)
        all_txs = all_txs.sort_values('timestamp').reset_index(drop=True)
        
        return all_txs
        
    except Exception as e:
        logger.error(f"Failed to fetch transactions from {exchange_name}: {e}")
        return pd.DataFrame()


def get_supported_exchanges() -> list[dict[str, str]]:
    """Get list of all CCXT-supported exchanges with info."""
    exchanges = [
        # Tier 1 (Most popular, best API)
        {'id': 'binance', 'name': 'Binance', 'tier': 1},
        {'id': 'coinbase', 'name': 'Coinbase', 'tier': 1},
        {'id': 'kraken', 'name': 'Kraken', 'tier': 1},
        {'id': 'okx', 'name': 'OKX', 'tier': 1},
        
        # Tier 2 (Very popular, good API)
        {'id': 'kucoin', 'name': 'KuCoin', 'tier': 2},
        {'id': 'huobi', 'name': 'Huobi', 'tier': 2},
        {'id': 'gate', 'name': 'Gate.io', 'tier': 2},
        {'id': 'bybit', 'name': 'Bybit', 'tier': 2},
        {'id': 'crypto', 'name': 'Crypto.com', 'tier': 2},
        {'id': 'mexc', 'name': 'MEXC', 'tier': 2},
        
        # Tier 3 (Popular, good API)
        {'id': 'bitfinex', 'name': 'Bitfinex', 'tier': 3},
        {'id': 'upbit', 'name': 'Upbit', 'tier': 3},
        {'id': 'bithumb', 'name': 'Bithumb', 'tier': 3},
        {'id': 'coinex', 'name': 'CoinEx', 'tier': 3},
        {'id': 'ftx', 'name': 'FTX', 'tier': 3},  # Note: FTX is currently defunct
        
        # More (100+ supported by CCXT)
        {'id': 'bitstamp', 'name': 'Bitstamp', 'tier': 4},
        {'id': 'gemini', 'name': 'Gemini', 'tier': 4},
        {'id': 'poloniex', 'name': 'Poloniex', 'tier': 4},
        {'id': 'hitbtc', 'name': 'HitBTC', 'tier': 4},
    ]
    
    return exchanges
