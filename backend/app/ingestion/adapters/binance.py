import pandas as pd
from .base import BaseAdapter

class BinanceAdapter(BaseAdapter):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # У Binance колонки часто называются так: 
        # 'UTC_Time', 'Account', 'Operation', 'Asset', 'Change', 'Remark'
        
        output = pd.DataFrame()
        
        # 1. Время (переводим в Unix timestamp)
        output['timestamp'] = pd.to_datetime(df['UTC_Time']).apply(lambda x: int(x.timestamp()))
        
        # 2. Актив
        output['asset'] = df['Asset'].str.upper()
        
        # 3. Количество (у Binance 'Change' может быть со знаком +/-)
        output['amount'] = df['Change'].abs()
        
        # 4. Тип операции
        # Нам нужно превратить их 'Deposit'/'Withdraw' в наши 'RECEIVE'/'TRANSFER'
        def map_type(op):
            op = op.lower()
            if 'deposit' in op: return 'RECEIVE'
            if 'withdraw' in op: return 'TRANSFER'
            if 'buy' in op: return 'BUY'
            if 'sell' in op: return 'SELL'
            return 'OTHER'
            
        output['type'] = df['Operation'].apply(map_type)
        
        # 5. Сеть и комиссия (если есть в Remark или отдельных колонках)
        output['network'] = 'binance_chain' # По умолчанию
        output['fee'] = 0.0
        
        return output