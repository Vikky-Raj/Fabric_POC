import os
import time
from agents.graph import graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(csv_path: str = None) -> dict:
    """Run the full agentic LangGraph pipeline end-to-end."""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, "bronze_sales_raw.csv")

    print("Starting agentic pipeline (LangGraph)...\n")
    start = time.time()

    result = graph.invoke({"csv_path": csv_path})

    elapsed = round(time.time() - start, 1)
    print(f"\nPipeline complete. 6 artifacts generated in output/ ({elapsed}s)")
    return result
