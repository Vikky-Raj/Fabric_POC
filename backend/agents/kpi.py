"""KPI Agent node — computes metrics from gold layer + AI interpretation."""

import os
import json
from datetime import datetime
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import PipelineState, get_llm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GOLD_DIR = os.path.join(OUTPUT_DIR, "gold")

SYSTEM_PROMPT = """You are a KPI Analyst Agent for a steel manufacturing data platform.
Interpret pre-computed KPI metrics and provide business-level insights.

Respond with valid JSON:
{
  "interpretation": "<2-3 paragraph business analysis>",
  "highlights": [
    {"metric": "<name>", "insight": "<key takeaway>"}
  ],
  "risks": ["<business risk>"],
  "recommendations": ["<actionable recommendation>"]
}"""


def run(state: PipelineState) -> dict:
    fact_sales = pd.read_parquet(os.path.join(GOLD_DIR, "fact_sales.parquet"))
    dim_customer = pd.read_parquet(os.path.join(GOLD_DIR, "dim_customer.parquet"))
    dim_region = pd.read_parquet(os.path.join(GOLD_DIR, "dim_region.parquet"))
    dim_product = pd.read_parquet(os.path.join(GOLD_DIR, "dim_product.parquet"))

    fact = fact_sales.merge(dim_region, on="region_id", how="left")

    total_revenue = float(fact["revenue"].sum())
    total_volume = float(fact["quantity_tons"].sum())
    asp = round(total_revenue / total_volume, 2) if total_volume > 0 else 0

    region_revenue = fact.groupby("region")["revenue"].sum()
    regional_contribution = {
        region: round(float(rev / total_revenue * 100), 1)
        for region, rev in region_revenue.items()
    }

    customer_orders = fact.groupby("customer_id")["order_id"].nunique()
    total_customers = len(customer_orders)
    repeat_customers = int((customer_orders > 1).sum())
    retention_rate = round(repeat_customers / total_customers * 100, 1) if total_customers > 0 else 0

    customer_revenue = fact.groupby("customer_id")["revenue"].sum()
    top_cid = customer_revenue.idxmax()
    top_cname = dim_customer.loc[dim_customer["customer_id"] == top_cid, "customer_name"].iloc[0]

    product_revenue = (
        fact.merge(dim_product, on="product_id", how="left")
        .groupby("product_name")["revenue"].sum()
        .to_dict()
    )

    kpis = {
        "computed_at": datetime.now().isoformat(),
        "metrics": {
            "total_revenue": total_revenue,
            "total_volume_tons": total_volume,
            "order_count": int(fact["order_id"].nunique()),
            "customer_count": total_customers,
        },
        "kpis": {
            "average_selling_price": asp,
            "regional_contribution": regional_contribution,
            "customer_retention_rate": retention_rate,
            "repeat_customers": repeat_customers,
            "total_customers": total_customers,
        },
        "top_customer": {"name": top_cname, "revenue": float(customer_revenue.max())},
        "revenue_by_region": {k: float(v) for k, v in region_revenue.items()},
        "revenue_by_product": {k: float(v) for k, v in product_revenue.items()},
    }

    llm = get_llm(json_mode=True)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze these KPIs:\n\n{json.dumps(kpis, indent=2)}"),
    ])
    kpis["ai_analysis"] = json.loads(response.content)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "kpi_report.json"), "w") as f:
        json.dump(kpis, f, indent=2)

    print("  ✓ KPI Agent — saved kpi_report.json")
    return {"kpi_report": kpis}
