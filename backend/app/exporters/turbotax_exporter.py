import io
import pandas as pd
from typing import Any

def export_turbotax_csv(lot_matches: list[dict[str, Any]]) -> io.BytesIO:
    """
    Generate a CSV compatible with TurboTax / TaxAct format.
    
    Columns:
    - Description (e.g. 1.5 BTC)
    - Date Acquired
    - Date Sold
    - Sales Proceeds
    - Cost Basis
    - Gain/Loss
    """
    rows = []
    for m in lot_matches:
        rows.append({
            "Description": f"{m['amount']:.8f} {m['asset']}",
            "Date Acquired": m["buy_timestamp"].strftime("%m/%d/%Y") if hasattr(m["buy_timestamp"], "strftime") else str(m["buy_timestamp"])[:10],
            "Date Sold": m["sell_timestamp"].strftime("%m/%d/%Y") if hasattr(m["sell_timestamp"], "strftime") else str(m["sell_timestamp"])[:10],
            "Sales Proceeds": round(m["proceeds"], 2),
            "Cost Basis": round(m["cost_basis"], 2),
            "Gain/Loss": round(m["gain_loss"], 2)
        })
    
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def export_koinly_compatible_csv(normalized_df: pd.DataFrame) -> io.BytesIO:
    """
    Export in a format that looks like Koinly's own export, 
    useful for users migrating or using other tools.
    """
    # Map our columns back to a standard format
    export_df = normalized_df.copy()
    # ... mapping logic ...
    output = io.BytesIO()
    export_df.to_csv(output, index=False)
    output.seek(0)
    return output
