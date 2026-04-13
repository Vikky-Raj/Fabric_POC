"""Ontology Agent node — generates JSON-LD business ontology from raw data."""

import os
import json
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import PipelineState, get_llm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

SYSTEM_PROMPT = """You are an Ontology Agent for a steel manufacturing data platform.
Analyze a raw dataset and generate a business ontology in JSON-LD format.

Respond with valid JSON:
{
  "@context": "https://schema.org/",
  "ontology_name": "<name>",
  "description": "<what this ontology represents>",
  "entities": [
    {
      "@type": "<EntityName>",
      "description": "<entity description>",
      "properties": [
        {
          "name": "<property_name>",
          "data_type": "<string|integer|float|date>",
          "description": "<meaning>",
          "source_column": "<original column>"
        }
      ]
    }
  ],
  "relationships": [
    {
      "subject": "<EntityName>",
      "predicate": "<relationship verb>",
      "object": "<EntityName>",
      "description": "<meaning>"
    }
  ],
  "business_glossary": [
    {
      "term": "<business term>",
      "definition": "<plain English definition>",
      "related_entity": "<EntityName>"
    }
  ]
}

Entities to detect: Customer, Product, SalesOrder, Region, TimePeriod.
Map relationships between them and create a business glossary."""


def run(state: PipelineState) -> dict:
    csv_path = state["csv_path"]
    df = pd.read_csv(csv_path)

    schema_info = [
        {
            "column": col,
            "dtype": str(df[col].dtype),
            "unique_values": int(df[col].nunique()),
            "samples": [str(v) for v in df[col].head(3).tolist()],
        }
        for col in df.columns
    ]

    user_prompt = (
        f"Generate a business ontology for this steel manufacturing sales dataset.\n\n"
        f"Schema ({len(df.columns)} columns, {len(df)} rows):\n"
        f"{json.dumps(schema_info, indent=2)}\n\n"
        f"Sample rows:\n{df.head(3).to_csv(index=False)}\n\n"
        f"This is ERP (SAP-like) sales data."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    ontology = json.loads(response.content)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "ontology.json"), "w") as f:
        json.dump(ontology, f, indent=2)

    print("  ✓ Ontology Agent — saved ontology.json")
    return {"ontology": ontology}
