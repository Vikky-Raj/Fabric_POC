"""Configuration — reads from environment variables.

Locally: loaded from .env file.
Azure App Service: set via App Settings (can use Key Vault references).
"""

import os
from dotenv import load_dotenv

# Load .env for local development; no-op if file doesn't exist
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

# Fabric Lakehouse endpoint (used by Data Factory pipeline, not by this API directly)
FABRIC_LAKEHOUSE_ENDPOINT = os.environ.get("FABRIC_LAKEHOUSE_ENDPOINT", "")
