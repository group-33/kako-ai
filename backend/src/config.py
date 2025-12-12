"""Application configuration and shared settings."""

import os
from dotenv import load_dotenv

import dspy

load_dotenv(override=True)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# --- Xentral API Configuration ---
# Loaded from .env (gitignored) so secrets stay out of git.
XENTRAL_API_KEY = os.getenv("XENTRAL_API_KEY")
XENTRAL_BASE_URL = os.getenv("XENTRAL_BASE_URL", "https://kako.xentral.biz/api/v1")
XENTRAL_TIMEOUT_SECONDS = 10

# --- Gemini model handles ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_3_PRO = dspy.LM("gemini/gemini-3-pro-preview", api_key=GOOGLE_API_KEY)
GEMINI_2_5_PRO = dspy.LM("gemini/gemini-2.5-pro", api_key=GOOGLE_API_KEY)
GEMINI_2_5_FLASH = dspy.LM("gemini/gemini-2.5-flash", api_key=GOOGLE_API_KEY)
GEMINI_2_5_FLASH_LITE = dspy.LM("gemini/gemini-2.5-flash-lite", api_key=GOOGLE_API_KEY)
