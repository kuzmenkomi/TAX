from __future__ import annotations
import networkx as nx
import pandas as pd

class TransactionGraph:
    def __init__(self, df: pd.DataFrame):
        self.G = nx.DiGraph()
        self._build_graph(df)

    def _build_graph(self, df: pd.DataFrame):
        """Строит направленные ребра между кошельками"""
        for _, tx in df.iterrows():
            f_wallet = str(tx.get("from_wallet", "")).strip()
            t_wallet = str(tx.get("to_wallet", "")).strip()
            
            if f_wallet and t_wallet:
                self.G.add_edge(
                    f_wallet, 
                    t_wallet, 
                    asset=tx["asset"],
                    network=tx.get("network", "unknown"),
                    timestamp=tx["timestamp"]
                )

    def verify_connection(self, source_wallet: str, target_wallet: str) -> bool:
        """Проверяет, есть ли путь в графе (прямой или через посредников)"""
        if not source_wallet or not target_wallet:
            return False
        if source_wallet == target_wallet:
            return True
        try:
            # Ищем, связаны ли эти узлы в структуре кошельков пользователя
            return nx.has_path(self.G, source_wallet, target_wallet)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return False

    def get_all_paths(self, start_node: str):
        """Возвращает все достижимые кошельки (для визуализации флоу)"""
        if start_node not in self.G: return []
        return list(nx.descendants(self.G, start_node))