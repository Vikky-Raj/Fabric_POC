"""Steel Sales Intelligence — Headless AI Agent API.

Designed to be called by Fabric Data Factory Web Activities.
Each POST endpoint accepts data as input and returns AI analysis.
No local file storage — data flows in/out via request/response.
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Steel Sales Intelligence API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────
class DiscoveryRequest(BaseModel):
    """CSV data summary for discovery profiling."""
    columns: list[dict]       # [{"name": ..., "dtype": ..., "nulls": ..., "unique": ..., "samples": [...]}]
    row_count: int
    column_count: int
    sample_rows_csv: str      # First 5 rows as CSV string
    filename: str = "bronze_data.csv"

class QualityRequest(BaseModel):
    """Pre-computed quality check results from Fabric notebook."""
    quality_report: dict      # Output of rule-based checks

class OntologyRequest(BaseModel):
    """Schema info for ontology generation."""
    schema_info: list[dict]   # [{"column": ..., "dtype": ..., "unique_values": ..., "samples": [...]}]
    row_count: int
    column_count: int
    sample_rows_csv: str
    filename: str = "bronze_data.csv"

class SemanticRequest(BaseModel):
    """Ontology + gold schema for semantic model generation."""
    ontology: dict
    gold_schemas: dict        # {"fact_sales": {"columns": [...], "dtypes": {...}, ...}, ...}

class KpiRequest(BaseModel):
    """Pre-computed KPI metrics for AI interpretation."""
    kpis: dict                # Computed metrics from Fabric notebook

class ChatRequest(BaseModel):
    """Chat message with context."""
    message: str
    gold_data_csv: str = ""   # Gold tables as CSV (optional)
    kpi_report: dict | None = None
    semantic_model: dict | None = None


# ──────────────────────────────────────────────
# Agent Endpoints
# ──────────────────────────────────────────────
@app.post("/api/agents/discovery")
def run_discovery(req: DiscoveryRequest):
    """Profile raw data and identify entities."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

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

    user_prompt = (
        f"Analyze this dataset:\n"
        f"- File: {req.filename}\n"
        f"- Rows: {req.row_count}, Columns: {req.column_count}\n\n"
        f"Column details:\n{json.dumps(req.columns, indent=2)}\n\n"
        f"Sample rows:\n{req.sample_rows_csv}\n\n"
        f"This is steel manufacturing sales data from an ERP system."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    report = json.loads(response.content)

    return {"status": "ok", "discovery_report": report}


@app.post("/api/agents/quality")
def run_quality(req: QualityRequest):
    """Analyze data quality results and produce AI narrative."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

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

    user_prompt = (
        f"Analyze this data quality report for steel manufacturing sales data.\n\n"
        f"Quality Report:\n{json.dumps(req.quality_report, indent=2)}\n\n"
        f"Provide a business-friendly narrative, explain each rule, flag risks, "
        f"and recommend improvements."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    analysis = json.loads(response.content)

    enriched = {"rule_based_checks": req.quality_report, "ai_analysis": analysis}
    return {"status": "ok", "quality_report": enriched}


@app.post("/api/agents/ontology")
def run_ontology(req: OntologyRequest):
    """Generate JSON-LD business ontology from schema."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

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

    user_prompt = (
        f"Generate a business ontology for this steel manufacturing sales dataset.\n\n"
        f"Schema ({req.column_count} columns, {req.row_count} rows):\n"
        f"{json.dumps(req.schema_info, indent=2)}\n\n"
        f"Sample rows:\n{req.sample_rows_csv}\n\n"
        f"This is ERP (SAP-like) sales data."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    ontology = json.loads(response.content)

    return {"status": "ok", "ontology": ontology}


@app.post("/api/agents/semantic")
def run_semantic(req: SemanticRequest):
    """Create semantic model from ontology + gold star schema."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

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

    user_prompt = (
        f"Create a semantic model for this steel sales data product.\n\n"
        f"Ontology:\n{json.dumps(req.ontology, indent=2)}\n\n"
        f"Gold layer tables:\n{json.dumps(req.gold_schemas, indent=2, default=str)}\n\n"
        f"Map columns to business names, define measures, define KPIs, and suggest visualizations."
    )

    llm = get_llm(json_mode=True)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
    model = json.loads(response.content)

    return {"status": "ok", "semantic_model": model}


@app.post("/api/agents/kpi")
def run_kpi(req: KpiRequest):
    """Interpret pre-computed KPI metrics with AI."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

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

    llm = get_llm(json_mode=True)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze these KPIs:\n\n{json.dumps(req.kpis, indent=2)}"),
    ])

    result = req.kpis.copy()
    result["ai_analysis"] = json.loads(response.content)

    return {"status": "ok", "kpi_report": result}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Chat copilot — accepts context inline (no local file reads)."""
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

    kpi_context = ""
    semantic_context = ""
    if req.kpi_report:
        kpi_context = f"\nKPI Report:\n{json.dumps(req.kpi_report, indent=2, default=str)}"
    if req.semantic_model:
        semantic_context = f"\nSemantic Model:\n{json.dumps(req.semantic_model, indent=2)}"

    system_prompt = (
        "You are an AI Sales Intelligence Copilot for a steel manufacturing company.\n"
        "Answer using ONLY the data below. Be precise with numbers.\n"
        "For chart answers, embed this JSON block:\n"
        '```chart\n{"type": "bar|pie", "title": "...", "data": [{"label": "...", "value": ...}]}\n```\n\n'
        f"DATA:\n{req.gold_data_csv}\n{kpi_context}\n{semantic_context}"
    )

    llm = get_llm()
    resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=req.message)])
    answer = resp.content

    chart_data = None
    if "```chart" in answer:
        try:
            start = answer.index("```chart") + len("```chart")
            end = answer.index("```", start)
            chart_data = json.loads(answer[start:end].strip())
            answer = (answer[:answer.index("```chart")] + answer[end + 3:]).strip()
        except (ValueError, json.JSONDecodeError):
            pass

    return {"response": answer, "chart_data": chart_data}
