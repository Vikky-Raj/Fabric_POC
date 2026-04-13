"""Shared pipeline state and LLM factory for all agent nodes."""

from typing import TypedDict
from langchain_openai import AzureChatOpenAI
import config


class PipelineState(TypedDict, total=False):
    csv_path: str
    discovery_report: dict
    pipeline_summary: dict
    quality_report: dict
    ontology: dict
    semantic_model: dict
    kpi_report: dict


def get_llm(json_mode: bool = False):
    """Create an AzureChatOpenAI instance. Set json_mode=True for structured JSON output."""
    llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_DEPLOYMENT,
        azure_endpoint=config.AZURE_ENDPOINT,
        api_key=config.AZURE_API_KEY,
        api_version=config.AZURE_API_VERSION,
        temperature=0.2,
    )
    return llm.bind(response_format={"type": "json_object"}) if json_mode else llm
