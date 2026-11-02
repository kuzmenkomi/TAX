import pandas as pd
import io
from .base import BaseParser

class NubankParser(BaseParser):
    """
    Parser for Nubank (Pix) statements.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Nubank CSV columns: Data, Valor, Identificador, Descrição
        # This is a simplification; real Nubank CSVs might vary.
        
        normalized = pd.DataFrame()
        normalized['timestamp'] = pd.to_datetime(df['Data'], dayfirst=True)
        normalized['amount'] = df['Valor']
        normalized['type'] = normalized['amount'].apply(lambda x: 'deposit' if x > 0 else 'withdrawal')
        normalized['amount'] = normalized['amount'].abs()
        normalized['asset'] = 'BRL'
        normalized['description'] = df['Descrição']
        normalized['external_id'] = df['Identificador']
        
        return normalized

class MercadoPagoParser(BaseParser):
    """
    Parser for Mercado Pago statements.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        # Expected Mercado Pago columns: fecha, monto, operacion, estado
        
        normalized = pd.DataFrame()
        normalized['timestamp'] = pd.to_datetime(df['fecha'])
        normalized['amount'] = df['monto']
        normalized['type'] = normalized['amount'].apply(lambda x: 'deposit' if x > 0 else 'withdrawal')
        normalized['amount'] = normalized['amount'].abs()
        normalized['asset'] = 'ARS' # Default for Argentina MP, could be MXN, etc.
        normalized['description'] = df['operacion']
        normalized['external_id'] = df['id_operacion'] if 'id_operacion' in df.columns else None
        
        return normalized

class GenericBankParser(BaseParser):
    """
    Generic parser that attempts to find date and amount columns automatically.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        df = pd.read_csv(io.BytesIO(content))
        
        normalized = pd.DataFrame()
        
        # Try to find date column
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'fecha' in c.lower() or 'data' in c.lower()]
        if date_cols:
            normalized['timestamp'] = pd.to_datetime(df[date_cols[0]])
            
        # Try to find amount column
        amount_cols = [c for c in df.columns if 'amount' in c.lower() or 'monto' in c.lower() or 'valor' in c.lower()]
        if amount_cols:
            normalized['amount'] = df[amount_cols[0]]
            normalized['type'] = normalized['amount'].apply(lambda x: 'deposit' if x > 0 else 'withdrawal')
            normalized['amount'] = normalized['amount'].abs()
            
        normalized['asset'] = 'USD' # Default
        normalized['exchange'] = 'generic_bank'
        
        return normalized
