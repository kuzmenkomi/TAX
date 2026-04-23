from __future__ import annotations
import pandas as pd
from typing import Any

# Импорты Splink 4.0+
from splink import Linker, SettingsCreator, DuckDBAPI
import splink.comparison_library as cl
import splink.comparison_level_library as cll

class ProbabilisticMatcher:
    def __init__(self, cfg: Any):
        self.max_amount_diff = cfg.max_amount_diff
        self.max_time_diff = cfg.max_time_diff_seconds

    def get_settings(self) -> dict[str, Any]:
        return {
            "link_type": "link_only",
            "comparisons": [
                cl.ExactMatch("asset"),
                # МЕНЯЕМ ЗДЕСЬ: Сеть теперь не обязана совпадать на 100%
                {
                    "output_column_name": "network",
                    "comparison_levels": [
                        cll.NullLevel("network"),
                        cll.ExactMatchLevel("network"), # Если сеть совпала — это жирный плюс
                        cll.ElseLevel(), # Если не совпала — мы всё равно рассматриваем вариант
                    ],
                },
                {
                    "output_column_name": "amount",
                    "comparison_levels": [
                        cll.NullLevel("amount"),
                        cll.ExactMatchLevel("amount"),
                        {
                            "sql_condition": f"ABS(amount_l - amount_r) <= {self.max_amount_diff}",
                            "label_for_charts": "Matching within gas/bridge fee range",
                        },
                        cll.ElseLevel(),
                    ],
                },
                {
                    "output_column_name": "timestamp",
                    "comparison_levels": [
                        cll.NullLevel("timestamp"),
                        {
                            "sql_condition": f"ABS(epoch(timestamp_l) - epoch(timestamp_r)) <= {self.max_time_diff}",
                            "label_for_charts": "Within bridge time window",
                        },
                        cll.ElseLevel(),
                    ],
                },
            ],
            # МЕНЯЕМ ЗДЕСЬ: Блокируем только по активу. 
            # Теперь мост (разные сети) попадет в выборку для анализа.
            "blocking_rules_to_generate_predictions": [
                "l.asset = r.asset", 
            ],
            "retain_matching_columns": True,
            "retain_intermediate_calculation_columns": False,
        }

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Запуск процесса вероятностного сопоставления"""
        working_df = df.copy()
        
        # Гарантируем наличие необходимых колонок
        if "unique_id" not in working_df.columns:
            working_df["unique_id"] = working_df.index.astype(str)
        
        if "network" not in working_df.columns:
            working_df["network"] = "unknown"

        # Разделяем датасет на две стороны для линковки
        transfers = working_df[working_df["type"] == "TRANSFER"]
        receives = working_df[working_df["type"] == "RECEIVE"]

        if transfers.empty or receives.empty:
            return pd.DataFrame()

        # Инициализация API и настроек (Splink 4 Style)
        db_api = DuckDBAPI()
        settings_obj = SettingsCreator(**self.get_settings())
        
        # Создаем линкер
        linker = Linker([transfers, receives], settings_obj, db_api)
        
        # Выполняем предсказание и возвращаем результат как Pandas DataFrame
        try:
            predictions = linker.inference.predict(threshold_match_probability=0.7)
            return predictions.as_pandas_dataframe()
        except Exception as e:
            print(f"Matching Error: {e}")
            return pd.DataFrame()