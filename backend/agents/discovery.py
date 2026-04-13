"""Discovery Agent node — profiles raw CSV and identifies entities."""

import os
import json
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import PipelineState, get_llm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

SYSTEM_PROMPT = """You are a Data Discovery Agent for a steel manufacturing company.
Analyze raw dataset schemas and produce a structured profiling report.

Respond with valid JSON:
{
  "dataset_name": "<name>",
  "row_count": <int>,
  "column_count": <int>,
  "columns": [
    {
      "name": "<column_name>",
      "inferred_type": "<string|integer|float|date|categorical>",
      "sample_values": ["<val1>", "<val2>", "<val3>"],
      "null_count": <int>,
      "unique_count": <int>,
      "observation": "<brief note>"
    }
  ],
  "entities": [
    {
      "entity_name": "<e.g. Customer, Product, SalesOrder>",
      "related_columns": ["<col1>", "<col2>"],
      "description": "<what this entity represents>"
    }
  ],
  "data_quality_observations": ["<observation1>", "<observation2>"],
  "summary": "<2-3 sentence summary>"
}"""


def run(state: PipelineState) -> dict:
    csv_path = state["csv_path"]
    df = pd.read_csv(csv_path)

    col_info = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "nulls": int(df[col].isnull().sum()),
            "unique": int(df[col].nunique()),
            "samples": [str(v) for v in df[col].head(3).tolist()],
        }
        for col in df.columns
    ]

    user_prompt = (
        f"Analyze this dataset:\n"
        f"- File: {os.path.basename(csv_path)}\n"
        f"- Rows: {len(df)}, Columns: {len(df.columns)}\n\n"
        f"Column details:\n{json.dumps(col_info, indent=2)}\n\n"
        f"Sample rows:\n{df.head(3).to_csv(index=False)}\n\n"
        f"This is steel manufacturing sales data from an ERP system."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    report = json.loads(response.content)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "discovery_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print("  ✓ Discovery Agent — saved discovery_report.json")
    return {"discovery_report": report}
