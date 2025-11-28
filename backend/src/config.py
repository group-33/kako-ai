"""Application configuration and shared settings."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM = "gpt-5-2025-08-07"

# Nexar API Credentials
NEXAR_CLIENT_ID = os.getenv("NEXAR_CLIENT_ID", "")
NEXAR_CLIENT_SECRET = os.getenv("NEXAR_CLIENT_SECRET", "")
if not NEXAR_CLIENT_ID or not NEXAR_CLIENT_SECRET:
    raise ValueError(
        "NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET must be set in environment variables (create .env file)."
    )
