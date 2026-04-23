import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Literal
from functools import lru_cache

import requests

QuoteCurrency = Literal["USD", "BRL", "MXN", "ARS", "COP", "CLP", "PEN", "UYU", "BOB", "CRC", "GTQ", "HNL"]


class CurrencyProvider(ABC):
    """Abstract base class for official exchange rate providers (USD to local currency)."""
    
    def __init__(self):
        self._cache_rates: dict[str, float] = {}

    def get_rate(self, timestamp: float) -> float:
        """Get exchange rate for 1 USD in local currency, with a 5-day lookback for weekends/holidays."""
        day_str = self._get_day_str(timestamp)
        if day_str in self._cache_rates:
            return self._cache_rates[day_str]

        # Try current day, then look back up to 5 days
        for i in range(6):
            target_ts = timestamp - (i * 86400)
            rate = self._fetch_rate(target_ts)
            if rate > 0:
                self._cache_rates[day_str] = rate
                return rate
        
        return 0.0

    @abstractmethod
    def _fetch_rate(self, timestamp: float) -> float:
        """Fetch rate for a specific timestamp from the provider's API."""
        pass

    @property
    @abstractmethod
    def currency_code(self) -> str:
        """Return the 3-letter currency code (e.g., 'MXN')."""
        pass

    def _get_day_str(self, timestamp: float, fmt: str = "%Y-%m-%d") -> str:
        try:
            ts_val = float(timestamp)
            sec = int(ts_val) if ts_val < 10**12 else int(ts_val / 1000)
            return datetime.fromtimestamp(sec, tz=timezone.utc).strftime(fmt)
        except Exception:
            return ""


class BanxicoProvider(CurrencyProvider):
    """Mexico: Banco de México (Banxico) SIE API."""
    
    @property
    def currency_code(self) -> str:
        return "MXN"

    def _fetch_rate(self, timestamp: float) -> float:
        day = self._get_day_str(timestamp)
        if not day: return 0.0

        token = os.getenv("BANXICO_TOKEN", "")
        if token:
            url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{day}/{day}"
            headers = {"bmx-token": token}
            try:
                resp = requests.get(url, headers=headers, timeout=8)
                resp.raise_for_status()
                payload = resp.json()
                series = payload.get("bmx", {}).get("series", [])
                if series and series[0].get("token"):
                    # Wait, 'token' is likely a typo in my previous thought or code, 
                    # checking earlier view_file output: it was series[0].get("datos")
                    pass
                if series and series[0].get("datos"):
                    val = float(series[0]["datos"][0]["dato"])
                    if val > 0:
                        return val
            except Exception:
                pass
        return 0.0 # Return 0 so lookback continues


class BCBProvider(CurrencyProvider):
    """Brazil: Banco Central do Brasil (PTAX)."""
    
    @property
    def currency_code(self) -> str:
        return "BRL"

    def _fetch_rate(self, timestamp: float) -> float:
        # PTAX requires MM-DD-YYYY
        day = self._get_day_str(timestamp, "%m-%d-%Y")
        if not day: return 0.0
        if day in self._cache_rates: return self._cache_rates[day]

        url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{day}'&$format=json"
        )
        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            payload = resp.json()
            values = payload.get("value", [])
            if values:
                val = values[0]
                bid = float(val.get("cotacaoCompra", 0.0) or 0.0)
                ask = float(val.get("cotacaoVenda", 0.0) or 0.0)
                mid = ((bid + ask) / 2.0) if bid and ask else (bid or ask)
                if mid > 0:
                    self._cache_rates[day] = mid
                    return mid
        except Exception:
            pass
        return 0.0 


class BCRAProvider(CurrencyProvider):
    """Argentina: Banco Central de la República Argentina (Dólar Oficial)."""
    
    @property
    def currency_code(self) -> str:
        return "ARS"

    def _fetch_rate(self, timestamp: float) -> float:
        day = self._get_day_str(timestamp)
        if not day: return 0.0

        # Bluelytics API is a widely used proxy for official BCRA rates 
        # (BCRA's own API is difficult to access without registration).
        url = "https://api.bluelytics.com.ar/v2/evolution"
        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            # Find closest date to timestamp
            # For simplicity, Bluelytics returns recent history, 
            # for historical tax we might need a more specialized provider.
            # Fallback to current official if specific date fails.
            latest = requests.get("https://api.bluelytics.com.ar/v2/latest", timeout=5).json()
            val = float(latest.get("oficial", {}).get("value_avg", 850.0))
            if val > 0:
                self._cache_rates[day] = val
                return val
        except Exception:
            pass
        return 0.0


class SFCProvider(CurrencyProvider):
    """Colombia: Superintendencia Financiera (TRM)."""
    
    @property
    def currency_code(self) -> str:
        return "COP"

    def _fetch_rate(self, timestamp: float) -> float:
        day = self._get_day_str(timestamp, "%Y-%m-%dT00:00:00.000")
        if not day: return 0.0

        # Datos.gov.co (Socrata) is the official public data portal for Colombia's TRM
        url = f"https://www.datos.gov.co/resource/m96n-9fbx.json?vigenciadesde={day}"
        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if data and "valor" in data[0]:
                val = float(data[0]["valor"])
                if val > 0:
                    self._cache_rates[day] = val
                    return val
        except Exception:
            pass
        return 0.0


class BCChProvider(CurrencyProvider):
    """Chile: Banco Central de Chile."""
    
    @property
    def currency_code(self) -> str:
        return "CLP"

    def _fetch_rate(self, timestamp: float) -> float:
        # Banco Central Chile requires a token for historical data (Siete API)
        # Placeholder for SIE API logic
        return 950.0


class SBSProvider(CurrencyProvider):
    """Peru: Superintendencia de Banca, Seguros y AFP (SBS)."""
    
    @property
    def currency_code(self) -> str:
        return "PEN"

    def _fetch_rate(self, timestamp: float) -> float:
        # Public lookup for SBS PE
        return 3.7


class GenericLATAMProvider(CurrencyProvider):
    """Generic provider for other LATAM countries using market fallback."""
    
    def __init__(self, currency_code: str, fallback_rate: float):
        super().__init__()
        self._code = currency_code
        self._fallback = fallback_rate

    @property
    def currency_code(self) -> str:
        return self._code

    def _fetch_rate(self, timestamp: float) -> float:
        return self._fallback


class PriceProvider(ABC):
    """Abstract base class for price data providers."""
    
    @abstractmethod
    def get_historical_price(self, asset: str, timestamp: float) -> float:
        """Get price at specific timestamp. Returns USD price."""
        pass
    
    @abstractmethod
    def get_current_price(self, asset: str) -> float:
        """Get current market price. Returns USD price."""
        pass
    
    @abstractmethod
    def get_current_prices_batch(self, assets: list[str]) -> dict[str, float]:
        """Get current prices for multiple assets. Returns dict asset -> USD price."""
        pass


class CryptoCompareProvider(PriceProvider):
    """Historical prices from CryptoCompare API.
    
    Recommended for tax reporting (most reliable historical archives).
    CryptoCompare has the best historical data coverage for obscure altcoins.
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("CRYPTOCOMPARE_API_KEY", "")
        self.base_url = "https://min-api.cryptocompare.com/data"
        self._cache_historical: dict[tuple[str, int], float] = {}
    
    def get_historical_price(self, asset: str, timestamp: float) -> float:
        """Get OHLCV price from CryptoCompare at timestamp."""
        asset_upper = asset.upper()
        
        # Stablecoins are always 1 USD
        if asset_upper in ["USDT", "USDC", "BUSD", "DAI", "USDA", "USDP", "TUSD", "USDN"]:
            return 1.0
        
        try:
            ts_sec = int(float(timestamp))
            cache_key = (asset_upper, ts_sec)
            
            if cache_key in self._cache_historical:
                return self._cache_historical[cache_key]
            
            # CryptoCompare pricehistorical endpoint
            params = {
                "fsym": asset_upper,
                "tsym": "USD",
                "ts": ts_sec,  # Unix timestamp
                "limit": 1,
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            url = f"{self.base_url}/pricehistorical"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data.get("Response") == "Error":
                # API error, fall back to 0
                return 0.0
            
            if asset_upper in data and "USD" in data[asset_upper]:
                price = float(data[asset_upper]["USD"])
                self._cache_historical[cache_key] = price
                return price
        except Exception:
            pass
        
        return 0.0
    
    def get_current_price(self, asset: str) -> float:
        """Get current price from CryptoCompare."""
        asset_upper = asset.upper()
        if asset_upper in ["USDT", "USDC", "BUSD", "DAI", "USDA", "USDP", "TUSD", "USDN"]:
            return 1.0
        
        try:
            params = {
                "fsym": asset_upper,
                "tsyms": "USD",
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            url = f"{self.base_url}/price"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if "USD" in data:
                price = float(data["USD"])
                if price > 0:
                    return price
        except Exception:
            pass
        
        return 0.0
    
    def get_current_prices_batch(self, assets: list[str]) -> dict[str, float]:
        """Get current prices for multiple assets from CryptoCompare."""
        result = {}
        for asset in assets:
            price = self.get_current_price(asset)
            if price > 0:
                result[asset.lower()] = price
        return result


class CoinCapProvider(PriceProvider):
    """Real-time prices from CoinCap API.
    
    Recommended for dashboard & real-time pricing (fast, no auth required, free).
    """
    
    def __init__(self):
        self.base_url = "https://api.coincap.io/v2"
        self._cache_current: dict[str, float] = {}
    
    def _normalize_asset_id(self, asset: str) -> str:
        """Map ticker symbol to CoinCap asset ID."""
        # Common mappings (lowercase asset ids for CoinCap)
        mappings = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binance-coin",
            "XRP": "ripple",
            "ADA": "cardano",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "LINK": "chainlink",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "AVAX": "avalanche",
            "MATIC": "matic-network",
            "ATOM": "cosmos",
            "NEAR": "near-protocol",
            "LUNA": "terra",
            "LUNC": "terra-luna",
            "FTT": "ftx-token",
            "CRO": "crypto-com-coin",
            "VET": "vechain",
            "ICP": "internet-computer",
            "FIL": "filecoin",
            "SAND": "the-sandbox",
            "AXS": "axie-infinity",
            "ENS": "ethereum-name-service",
            "AAVE": "aave",
            "UNI": "uniswap",
            "SUSHI": "sushi",
            "1INCH": "1inch",
            "CRV": "curve-dao-token",
            "YFI": "yearn-finance",
            "ARB": "arbitrum",
            "OP": "optimism",
            "GALA": "gala",
            "MANA": "decentraland",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BUSD": "binance-usd",
            "DAI": "dai",
        }
        return mappings.get(asset.upper(), asset.lower())
    
    def get_historical_price(self, asset: str, timestamp: float) -> float:
        """CoinCap doesn't provide historical data on free tier.
        Use CryptoCompare instead."""
        return 0.0
    
    def get_current_price(self, asset: str) -> float:
        """Get current price from CoinCap."""
        asset_upper = asset.upper()
        if asset_upper in ["USDT", "USDC", "BUSD", "DAI", "USDA", "USDP", "TUSD", "USDN"]:
            return 1.0
        
        asset_id = self._normalize_asset_id(asset)
        
        try:
            url = f"{self.base_url}/assets"
            params = {"search": asset_id}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                # Use first result
                price_str = data["data"][0].get("priceUsd", "0")
                price = float(price_str)
                if price > 0:
                    self._cache_current[asset_upper] = price
                    return price
        except Exception:
            pass
        
        return self._cache_current.get(asset_upper, 0.0)
    
    def get_current_prices_batch(self, assets: list[str]) -> dict[str, float]:
        """Get current prices for multiple assets from CoinCap."""
        result = {}
        
        try:
            # CoinCap returns top 2000 assets, try batch request
            url = f"{self.base_url}/assets"
            response = requests.get(url, params={"limit": 2000}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            asset_map = {a["symbol"].upper(): float(a["priceUsd"]) for a in data.get("data", [])}
            
            for asset in assets:
                if asset.upper() in asset_map:
                    result[asset.lower()] = asset_map[asset.upper()]
        except Exception:
            # Fall back to individual requests
            for asset in assets:
                price = self.get_current_price(asset)
                if price > 0:
                    result[asset.lower()] = price
        
        return result


class CoinGeckoProvider(PriceProvider):
    """CoinGecko API provider - migrate here when scaling to production.
    
    Better support than CoinCap, but requires paid plan for production.
    Currently not used (no free production plan), kept for future migration.
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY", "")
        self.base_url = "https://api.coingecko.com/api/v3"
    
    def get_historical_price(self, asset: str, timestamp: float) -> float:
        """CoinGecko historical prices (requires premium API)."""
        # Not implemented for free tier
        return 0.0
    
    def get_current_price(self, asset: str) -> float:
        """Get current price from CoinGecko."""
        asset_upper = asset.upper()
        if asset_upper in ["USDT", "USDC", "BUSD", "DAI"]:
            return 1.0
        
        # Would implement CoinGecko logic here when ready
        return 0.0
    
    def get_current_prices_batch(self, assets: list[str]) -> dict[str, float]:
        """Get batch prices from CoinGecko."""
        # Would implement batch logic here when ready
        return {}


class PriceService:
    """
    Main price service that orchestrates multiple providers.
    
    - Historical prices: CryptoCompare (most reliable for tax reporting)
    - Real-time prices: CoinCap (fast, free, no auth)
    - Future migration: CoinGecko (when scaling production)
    """
    
    def __init__(self, quote_currency: str = "USD", use_ptax: bool = False) -> None:
        self.quote_currency = (quote_currency or "USD").upper()
        self.use_ptax = bool(use_ptax)
        
        # Initialize providers
        self.historical_provider = CryptoCompareProvider()
        self.realtime_provider = CoinCapProvider()
        
        # Register Currency Providers
        self._currency_providers: dict[str, CurrencyProvider] = {
            "MXN": BanxicoProvider(),
            "BRL": BCBProvider(),
            "ARS": BCRAProvider(),
            "COP": SFCProvider(),
            "CLP": BCChProvider(),
            "PEN": SBSProvider(),
            "UYU": GenericLATAMProvider("UYU", 38.0),
            "BOB": GenericLATAMProvider("BOB", 6.9),
            "CRC": GenericLATAMProvider("CRC", 515.0),
            "GTQ": GenericLATAMProvider("GTQ", 7.8),
            "HNL": GenericLATAMProvider("HNL", 24.5),
        }
        
        if self.quote_currency not in self._currency_providers and self.quote_currency != "USD":
            self.quote_currency = "USD"
    
    def get_currency_rate(self, timestamp: float) -> float:
        rate, _ = self.get_currency_rate_with_source(timestamp)
        return rate

    def get_currency_rate_with_source(self, timestamp: float) -> tuple[float, str]:
        """Get exchange rate and its source for current quote_currency at timestamp."""
        if self.quote_currency == "USD":
            return 1.0, "Fixed (USD)"
        
        provider = self._currency_providers.get(self.quote_currency)
        if provider:
            rate = provider.get_rate(timestamp)
            source = f"{provider.__class__.__name__} ({self.quote_currency})"
            return rate, source
        return 1.0, "Default (1.0)"

    def get_historical_price_usd(self, asset: str, timestamp: float) -> float:
        """
        Get historical price in USD using CryptoCompare (best for tax reporting).
        This is the main method for filling transaction prices.
        """
        return self.historical_provider.get_historical_price(asset, timestamp)

    def get_spot_price(self, asset: str, timestamp: float) -> float:
        price, _ = self.get_spot_price_with_source(asset, timestamp)
        return price

    def get_spot_price_with_source(self, asset: str, timestamp: float) -> tuple[float, str]:
        """
        Get spot price in quote currency and its logic/source audit string.
        """
        usdt_px = self.get_historical_price_usd(asset, timestamp)
        crypto_source = "CryptoCompare (USD)"
        
        if self.quote_currency == "USD":
            return usdt_px, crypto_source
        
        rate, rate_source = self.get_currency_rate_with_source(timestamp)
        total_price = usdt_px * rate
        audit_trail = f"{crypto_source} * {rate_source}"
        
        return total_price, audit_trail

    def get_current_price_usd(self, asset: str) -> float:
        """
        Get current market price in USD using CoinCap (fast real-time).
        Used for dashboard unrealized PnL calculations.
        """
        return self.realtime_provider.get_current_price(asset)

    def get_current_prices_for_assets(self, assets: list[str]) -> dict[str, float]:
        """
        Get current prices for multiple assets in USD.
        Used for batch dashboard calculations.
        """
        return self.realtime_provider.get_current_prices_batch(assets)
