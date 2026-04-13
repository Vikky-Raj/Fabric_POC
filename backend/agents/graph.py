"""LangGraph StateGraph — wires all agent nodes into an executable pipeline.

Graph:
  START → discovery → data_pipeline → quality → ontology → semantic → kpi → END

Each node reads from PipelineState and returns a partial state update.
Data flows through typed state; heavy data (DataFrames) is passed via Parquet on disk.
"""

from langgraph.graph import StateGraph, START, END
from agents.state import PipelineState
from agents import discovery, data_pipeline, quality, ontology, semantic, kpi

builder = StateGraph(PipelineState)

builder.add_node("discovery_agent", discovery.run)
builder.add_node("data_pipeline", data_pipeline.run)
builder.add_node("quality_agent", quality.run)
builder.add_node("ontology_agent", ontology.run)
builder.add_node("semantic_agent", semantic.run)
builder.add_node("kpi_agent", kpi.run)

builder.add_edge(START, "discovery_agent")
builder.add_edge("discovery_agent", "data_pipeline")
builder.add_edge("data_pipeline", "quality_agent")
builder.add_edge("quality_agent", "ontology_agent")
builder.add_edge("ontology_agent", "semantic_agent")
builder.add_edge("semantic_agent", "kpi_agent")
builder.add_edge("kpi_agent", END)

graph = builder.compile()
