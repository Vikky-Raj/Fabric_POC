"""Quality Agent node — rule-based checks + AI-powered analysis."""

import os
import json
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import PipelineState, get_llm
from pipeline.quality import run_quality_checks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SILVER_PATH = os.path.join(OUTPUT_DIR, "silver", "silver_sales.parquet")

SYSTEM_PROMPT = """You are a Data Quality Agent for a steel manufacturing data platform.
Analyze a data quality report and produce an AI-powered narrative.

Respond with valid JSON:
{
  "overall_status": "<healthy|warning|critical>",
  "score": <0-100>,
  "narrative": "<2-3 paragraph analysis>",
  "findings": [
    {
      "rule": "<rule name>",
      "status": "<pass|fail>",
      "severity": "<info|warning|critical>",
      "explanation": "<business-level meaning>",
      "recommendation": "<what to do>"
    }
  ],
  "risks": ["<risk1>", "<risk2>"],
  "recommendations": ["<recommendation1>", "<recommendation2>"]
}"""


def run(state: PipelineState) -> dict:
    silver_df = pd.read_parquet(SILVER_PATH)
    quality_report = run_quality_checks(silver_df)

    user_prompt = (
        f"Analyze this data quality report for steel manufacturing sales data.\n\n"
        f"Quality Report:\n{json.dumps(quality_report, indent=2)}\n\n"
        f"Provide a business-friendly narrative, explain each rule, flag risks, "
        f"and recommend improvements."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    analysis = json.loads(response.content)

    enriched = {"rule_based_checks": quality_report, "ai_analysis": analysis}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "quality_report.json"), "w") as f:
        json.dump(enriched, f, indent=2)

    print("  ✓ Quality Agent — saved quality_report.json")
    return {"quality_report": enriched}
