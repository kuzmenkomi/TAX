from typing import Dict, Type
from .adapters.base import BaseAdapter
from .adapters.binance import BinanceAdapter
from .adapters.bybit import BybitAdapter
from .adapters.coinbase import CoinbaseAdapter
from .adapters.foxbit import FoxbitAdapter
from .adapters.mercado_bitcoin import MercadoBitcoinAdapter
from .adapters.novadax import NovaDaxAdapter

class AdapterRegistry:
    _adapters: Dict[str, Type[BaseAdapter]] = {
        "binance": BinanceAdapter,
        "bybit": BybitAdapter,
        "coinbase": CoinbaseAdapter,
        "mercado_bitcoin": MercadoBitcoinAdapter,
        "foxbit": FoxbitAdapter,
        "novadax": NovaDaxAdapter,
    }

    @classmethod
    def get_adapter(cls, name: str) -> BaseAdapter:
        adapter_class = cls._adapters.get(name.lower())
        if not adapter_class:
            raise ValueError(f"Формат {name} пока не поддерживается.")
        return adapter_class()