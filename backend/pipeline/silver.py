import pandas as pd


# Bronze → Silver column mapping (from BRD & Bronze Layer doc)
COLUMN_MAP = {
    "sales_doc": "order_id",
    "sales_item": "order_item",
    "doc_date": "order_date",
    "customer_code": "customer_id",
    "customer_full_name": "customer_name",
    "material_code": "product_id",
    "material_desc": "product_name",
    "steel_type": "steel_type",
    "region_text": "region",
    "order_qty": "quantity_tons",
    "qty_uom": "uom",
    "net_price": "unit_price",
    "price_currency": "currency",
    "net_value": "revenue",
    "plant_code": "plant_code",
    "created_timestamp": "ingestion_timestamp",
}


def transform_to_silver(bronze_df: pd.DataFrame) -> pd.DataFrame:
    """Clean, standardize, and deduplicate bronze data into silver layer."""
    df = bronze_df.copy()

    # 1. Rename columns to business-friendly names
    df = df.rename(columns=COLUMN_MAP)

    # 2. Convert date from YYYYMMDD integer to proper datetime
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y%m%d")

    # 3. Parse ingestion timestamp
    df["ingestion_timestamp"] = pd.to_datetime(df["ingestion_timestamp"])

    # 4. Deduplicate on (order_id, order_item)
    df = df.drop_duplicates(subset=["order_id", "order_item"], keep="first")

    # 5. Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 6. Reset index
    df = df.reset_index(drop=True)

    return df
