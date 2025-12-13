"""Application configuration and shared settings."""
import os
from dotenv import load_dotenv

import dspy

load_dotenv(override=True)


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "backend/src/kako-ai_auth.json"
VERTEX_ARGS = {
    "project": "kako-ai-480517",
    "vertex_location": "europe-west3"
}

# Nexar API Credentials
NEXAR_CLIENT_ID = os.getenv("NEXAR_CLIENT_ID", "")
NEXAR_CLIENT_SECRET = os.getenv("NEXAR_CLIENT_SECRET", "")
_procurement_api_is_live_env = os.getenv("PROCUREMENT_API_IS_LIVE", "false").lower() == "true"
# Only enable "live" calls when credentials are present; otherwise the procurement
# tooling falls back to cached/mock behavior without preventing the API from booting.
PROCUREMENT_API_IS_LIVE = bool(_procurement_api_is_live_env and NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET)

# --- Xentral API Configuration ---
# Loaded from .env (gitignored) so secrets stay out of git.
XENTRAL_BEARER_TOKEN = os.getenv("XENTRAL_BEARER_TOKEN")
XENTRAL_BASE_URL = os.getenv("XENTRAL_BASE_URL")
XENTRAL_TIMEOUT_SECONDS = 10
SUPABASE_DSN = os.getenv("SUPABASE_DSN")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")

# --- Gemini model handles ---
GEMINI_3_PRO = dspy.LM("vertex_ai/gemini-3-pro-preview", **VERTEX_ARGS)
GEMINI_2_5_PRO = dspy.LM("vertex_ai/gemini-2.5-pro", **VERTEX_ARGS)
GEMINI_2_5_FLASH = dspy.LM("vertex_ai/gemini-2.5-flash", **VERTEX_ARGS)
GEMINI_2_5_FLASH_LITE = dspy.LM("gemini-2.5-flash-lite", **VERTEX_ARGS)
GEMINI_1_5_PRO = dspy.LM("vertex_ai/gemini-1.5-pro", **VERTEX_ARGS)