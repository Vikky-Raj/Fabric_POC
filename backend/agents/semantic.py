"""Semantic Agent node — creates semantic model from ontology + gold schema."""

import os
import json
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import PipelineState, get_llm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GOLD_DIR = os.path.join(OUTPUT_DIR, "gold")

SYSTEM_PROMPT = """You are a Semantic Modeling Agent for a steel manufacturing data platform.
Create a business-friendly semantic layer from ontology + gold star schema.

Respond with valid JSON:
{
  "model_name": "Steel_Sales_Intelligence_DP",
  "description": "<what this semantic model provides>",
  "column_mappings": [
    {
      "technical": "<gold column>",
      "business": "<business name>",
      "table": "<gold table>",
      "description": "<meaning>"
    }
  ],
  "measures": [
    {
      "name": "<measure>",
      "expression": "<aggregation e.g. SUM(revenue)>",
      "format": "<currency|number|percentage>",
      "description": "<what it computes>"
    }
  ],
  "kpi_definitions": [
    {
      "name": "<KPI>",
      "formula": "<calculation>",
      "business_question": "<what question it answers>",
      "target": "<optional benchmark>"
    }
  ],
  "recommended_visualizations": [
    {
      "name": "<chart title>",
      "type": "<bar|line|pie|card|table>",
      "measures": ["<measure1>"],
      "dimensions": ["<dimension1>"],
      "description": "<insight>"
    }
  ]
}

Required KPIs: Revenue Growth %, Customer Retention Rate, ASP, Regional Sales Contribution %."""


def run(state: PipelineState) -> dict:
    ontology = state["ontology"]

    gold_schemas = {}
    if os.path.exists(GOLD_DIR):
        for fname in os.listdir(GOLD_DIR):
            if fname.endswith(".parquet"):
                df = pd.read_parquet(os.path.join(GOLD_DIR, fname))
                gold_schemas[fname[:-8]] = {
                    "columns": list(df.columns),
                    "dtypes": {col: str(df[col].dtype) for col in df.columns},
                    "row_count": len(df),
                    "sample": df.head(2).to_dict(orient="records"),
                }

    user_prompt = (
        f"Create a semantic model for this steel sales data product.\n\n"
        f"Ontology:\n{json.dumps(ontology, indent=2)}\n\n"
        f"Gold layer tables:\n{json.dumps(gold_schemas, indent=2, default=str)}\n\n"
        f"Map columns to business names, define measures, define KPIs, and suggest visualizations."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    model = json.loads(response.content)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "semantic_model.json"), "w") as f:
        json.dump(model, f, indent=2)

    print("  ✓ Semantic Agent — saved semantic_model.json")
    return {"semantic_model": model}
