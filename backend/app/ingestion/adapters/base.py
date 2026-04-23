from abc import ABC, abstractmethod
import pandas as pd

class BaseAdapter(ABC):
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Метод для преобразования сырого CSV биржи в наш формат"""
        pass