import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_CSV = os.path.join(BASE_DIR, "bronze_sales_raw.csv")


def load_bronze(path: str = BRONZE_CSV) -> pd.DataFrame:
    """Load the raw bronze CSV file as-is into a DataFrame."""
    df = pd.read_csv(path)
    return df
