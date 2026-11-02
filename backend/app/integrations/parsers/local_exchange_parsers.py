import pandas as pd
import io
from .base import BaseParser

class LemonCashParser(BaseParser):
    """
    Parser for Lemon Cash (Argentina/Mexico) CSV exports.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Lemon columns: Created At, Type, Asset, Amount, Price USD, Total USD
        
        normalized = self._get_empty_df()
        normalized['timestamp'] = pd.to_datetime(df['Created At'])
        normalized['asset'] = df['Asset']
        normalized['type'] = df['Type'].str.lower() # buy, sell, deposit, withdrawal
        normalized['amount'] = df['Amount']
        normalized['price'] = df.get('Price USD', 0)
        normalized['fee'] = 0 # Usually included in price or not explicit in basic CSV
        normalized['exchange'] = 'lemoncash'
        normalized['external_id'] = df.get('ID', None)
        
        return normalized

class BeloParser(BaseParser):
    """
    Parser for Belo (Argentina) CSV exports.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Belo columns: date, type, currency, amount, balance
        
        normalized = self._get_empty_df()
        normalized['timestamp'] = pd.to_datetime(df['date'])
        normalized['asset'] = df['currency']
        normalized['type'] = df['type'].str.lower()
        normalized['amount'] = df['amount']
        normalized['exchange'] = 'belo'
        
        return normalized

class BuenbitParser(BaseParser):
    """
    Parser for Buenbit (Argentina) CSV exports.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Buenbit columns: date, operation, asset, amount, status
        normalized = self._get_empty_df()
        normalized['timestamp'] = pd.to_datetime(df['date'])
        normalized['asset'] = df['asset']
        normalized['type'] = df['operation'].str.lower()
        normalized['amount'] = df['amount']
        normalized['exchange'] = 'buenbit'
        return normalized

class OrionxParser(BaseParser):
    """
    Parser for Orionx (Chile) CSV exports.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Orionx columns: date, type, main_asset, amount, price, fee
        normalized = self._get_empty_df()
        normalized['timestamp'] = pd.to_datetime(df['date'])
        normalized['asset'] = df['main_asset']
        normalized['type'] = df['type'].str.lower()
        normalized['amount'] = df['amount']
        normalized['price'] = df.get('price', 0)
        normalized['fee'] = df.get('fee', 0)
        normalized['exchange'] = 'orionx'
        return normalized

class BinanceParser(BaseParser):
    """
    Parser for Binance Spot Trade History CSV exports.
    Supports column variants:
      - Pair / Market
      - Side / Type
      - Executed / Amount
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        columns = df.columns.tolist()

        # Resolve column name variants
        pair_col     = 'Pair'     if 'Pair'     in columns else 'Market'
        side_col     = 'Side'     if 'Side'     in columns else 'Type'
        executed_col = 'Executed' if 'Executed' in columns else 'Amount'

        normalized = self._get_empty_df()
        normalized['timestamp'] = pd.to_datetime(df['Date(UTC)'])
        normalized['asset'] = (
            df[pair_col]
            .str.replace('USDT', '', regex=False)
            .str.replace('BUSD', '', regex=False)
        )
        normalized['type'] = df[side_col].str.lower()  # buy, sell
        normalized['amount'] = df[executed_col]
        normalized['price'] = df['Price']
        normalized['fee'] = df['Fee']
        normalized['exchange'] = 'binance'

        return normalized

def get_parser_for_exchange(exchange_id: str) -> BaseParser:
    """
    Factory to return the correct CSV parser for a local exchange.
    """
    parsers = {
        "lemon": LemonCashParser(),
        "belo": BeloParser(),
        "buenbit": BuenbitParser(),
        "orionx": OrionxParser(),
        "binance": BinanceParser(),
    }
    return parsers.get(exchange_id.lower())
