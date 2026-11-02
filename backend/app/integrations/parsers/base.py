from abc import ABC, abstractmethod
from typing import Any, List
import pandas as pd
import io

class BaseParser(ABC):
    """
    Abstract base class for all CSV/JSON parsers (Banks and Exchanges).
    """
    
    @abstractmethod
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse raw bytes and return a normalized pandas DataFrame.
        Expected columns: timestamp, asset, type, amount, price, fee, fee_asset, exchange, external_id
        """
        pass

    def _get_empty_df(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            'timestamp', 'asset', 'type', 'amount', 'price', 
            'fee', 'fee_asset', 'exchange', 'external_id'
        ])
