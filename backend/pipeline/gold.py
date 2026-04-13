import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_GOLD = os.path.join(BASE_DIR, "output", "gold")


def build_gold_layer(silver_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build star schema (fact + dimensions) from silver data and save as Parquet."""
    os.makedirs(OUTPUT_GOLD, exist_ok=True)

    # --- Dimension: dim_customer ---
    dim_customer = (
        silver_df[["customer_id", "customer_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # --- Dimension: dim_product ---
    dim_product = (
        silver_df[["product_id", "product_name", "steel_type"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # --- Dimension: dim_region ---
    dim_region = (
        silver_df[["region"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_region.insert(0, "region_id", range(1, len(dim_region) + 1))

    # --- Dimension: dim_time ---
    dim_time = pd.DataFrame({"date": silver_df["order_date"].unique()})
    dim_time["date"] = pd.to_datetime(dim_time["date"])
    dim_time = dim_time.sort_values("date").reset_index(drop=True)
    dim_time["month"] = dim_time["date"].dt.month
    dim_time["quarter"] = dim_time["date"].dt.quarter
    dim_time["year"] = dim_time["date"].dt.year
    dim_time["month_name"] = dim_time["date"].dt.strftime("%B")

    # --- Fact: fact_sales ---
    # Map region to region_id
    region_map = dict(zip(dim_region["region"], dim_region["region_id"]))

    fact_sales = silver_df[
        [
            "order_id",
            "order_item",
            "order_date",
            "customer_id",
            "product_id",
            "region",
            "quantity_tons",
            "unit_price",
            "revenue",
            "currency",
            "plant_code",
        ]
    ].copy()
    fact_sales["region_id"] = fact_sales["region"].map(region_map)
    fact_sales = fact_sales.drop(columns=["region"])

    # Save all tables as Parquet
    tables = {
        "fact_sales": fact_sales,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_region": dim_region,
        "dim_time": dim_time,
    }
    for name, df in tables.items():
        df.to_parquet(os.path.join(OUTPUT_GOLD, f"{name}.parquet"), index=False)

    return tables
