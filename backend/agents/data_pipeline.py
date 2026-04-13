"""Data Pipeline node — Bronze → Silver → Gold transformation (no LLM)."""

import os
from agents.state import PipelineState
from pipeline.bronze import load_bronze
from pipeline.silver import transform_to_silver
from pipeline.gold import build_gold_layer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SILVER_DIR = os.path.join(BASE_DIR, "output", "silver")


def run(state: PipelineState) -> dict:
    csv_path = state["csv_path"]

    bronze_df = load_bronze(csv_path)
    silver_df = transform_to_silver(bronze_df)

    os.makedirs(SILVER_DIR, exist_ok=True)
    silver_df.to_parquet(os.path.join(SILVER_DIR, "silver_sales.parquet"), index=False)

    gold_tables = build_gold_layer(silver_df)

    summary = {
        "bronze_rows": len(bronze_df),
        "silver_rows": len(silver_df),
        "gold_tables": {name: len(df) for name, df in gold_tables.items()},
    }

    print("  ✓ Data Pipeline — Bronze → Silver → Gold")
    return {"pipeline_summary": summary}
