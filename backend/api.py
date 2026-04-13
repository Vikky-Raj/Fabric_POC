import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import pandas as pd

app = FastAPI(title="Steel Sales Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GOLD_DIR = os.path.join(OUTPUT_DIR, "gold")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


def _load_json(filename: str) -> dict:
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, f"{filename} not found. Upload and process data first.")
    with open(path) as f:
        return json.load(f)


def _load_gold_context() -> str:
    parts = []
    if os.path.exists(GOLD_DIR):
        for fname in sorted(os.listdir(GOLD_DIR)):
            if fname.endswith(".parquet"):
                df = pd.read_parquet(os.path.join(GOLD_DIR, fname))
                parts.append(
                    f"Table: {fname[:-8]} ({len(df)} rows)\n"
                    f"Columns: {list(df.columns)}\n"
                    f"Data:\n{df.to_csv(index=False)}"
                )
    return "\n\n".join(parts)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    chart_data: dict | None = None


@app.get("/api/status")
def get_status():
    """Check if data has been processed."""
    return {"ready": os.path.exists(os.path.join(OUTPUT_DIR, "kpi_report.json"))}


@app.post("/api/reset")
def reset_pipeline():
    """Delete all output so a new file can be uploaded."""
    import shutil
    for d in [OUTPUT_DIR, UPLOAD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
    return {"status": "reset"}


@app.post("/api/upload")
async def upload_and_process(file: UploadFile = File(...)):
    """Upload a CSV file and run the full agentic pipeline."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, "bronze_data.csv")

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    from orchestrator import run

    try:
        results = run(csv_path=save_path)
        return {"status": "completed", "summary": results.get("pipeline_summary", {})}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/kpis")
def get_kpis():
    return _load_json("kpi_report.json")

@app.get("/api/ontology")
def get_ontology():
    return _load_json("ontology.json")

@app.get("/api/quality")
def get_quality():
    return _load_json("quality_report.json")

@app.get("/api/semantic")
def get_semantic():
    return _load_json("semantic_model.json")

@app.get("/api/discovery")
def get_discovery():
    return _load_json("discovery_report.json")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.state import get_llm

    gold_context = _load_gold_context()

    kpi_context = ""
    semantic_context = ""
    try:
        kpi_context = f"\nKPI Report:\n{json.dumps(_load_json('kpi_report.json'), indent=2, default=str)}"
    except Exception:
        pass
    try:
        semantic_context = f"\nSemantic Model:\n{json.dumps(_load_json('semantic_model.json'), indent=2)}"
    except Exception:
        pass

    system_prompt = (
        "You are an AI Sales Intelligence Copilot for a steel manufacturing company.\n"
        "Answer using ONLY the data below. Be precise with numbers.\n"
        "For chart answers, embed this JSON block:\n"
        '```chart\n{"type": "bar|pie", "title": "...", "data": [{"label": "...", "value": ...}]}\n```\n\n'
        f"DATA:\n{gold_context}\n{kpi_context}\n{semantic_context}"
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

    return ChatResponse(response=answer, chart_data=chart_data)
