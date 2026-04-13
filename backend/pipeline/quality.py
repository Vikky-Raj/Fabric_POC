import os
import json
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def run_quality_checks(silver_df: pd.DataFrame) -> dict:
    """Run data quality rules on silver data and return a pass/fail report."""
    rules = []

    # Rule 1: No null revenue
    null_revenue = int(silver_df["revenue"].isnull().sum())
    rules.append({
        "rule": "No null revenue",
        "passed": null_revenue == 0,
        "detail": f"{null_revenue} null values found",
    })

    # Rule 2: Quantity > 0
    bad_qty = int((silver_df["quantity_tons"] <= 0).sum())
    rules.append({
        "rule": "Quantity greater than zero",
        "passed": bad_qty == 0,
        "detail": f"{bad_qty} rows with quantity <= 0",
    })

    # Rule 3: Valid customer IDs (non-null, non-empty)
    invalid_cust = int(silver_df["customer_id"].isnull().sum() + (silver_df["customer_id"] == "").sum())
    rules.append({
        "rule": "Valid customer IDs",
        "passed": invalid_cust == 0,
        "detail": f"{invalid_cust} invalid customer IDs",
    })

    # Rule 4: Valid product IDs (non-null, non-empty)
    invalid_prod = int(silver_df["product_id"].isnull().sum() + (silver_df["product_id"] == "").sum())
    rules.append({
        "rule": "Valid product IDs",
        "passed": invalid_prod == 0,
        "detail": f"{invalid_prod} invalid product IDs",
    })

    # Rule 5: No duplicate (order_id, order_item)
    dup_count = int(silver_df.duplicated(subset=["order_id", "order_item"]).sum())
    rules.append({
        "rule": "No duplicate order lines",
        "passed": dup_count == 0,
        "detail": f"{dup_count} duplicate rows found",
    })

    passed = sum(1 for r in rules if r["passed"])
    report = {
        "checked_at": datetime.now().isoformat(),
        "total": len(rules),
        "passed": passed,
        "failed": len(rules) - passed,
        "rules": rules,
    }

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "quality_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    return report
