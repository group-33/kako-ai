"""Application configuration and shared settings."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM Configuration
# LLM = "gpt-5-2025-08-07"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PROCUREMENT_LLM_MODEL = "gemini/gemini-2.0-flash"

# Nexar API Credentials
NEXAR_CLIENT_ID = os.getenv("NEXAR_CLIENT_ID", "")
NEXAR_CLIENT_SECRET = os.getenv("NEXAR_CLIENT_SECRET", "")
PROCUREMENT_API_IS_LIVE = (
    os.getenv("PROCUREMENT_API_IS_LIVE", "false").lower() == "true"
)

if not NEXAR_CLIENT_ID or not NEXAR_CLIENT_SECRET:
    raise ValueError(
        "NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET must be set in environment variables (create .env file)."
    )
