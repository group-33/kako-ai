"""Application configuration and shared settings."""

import os
from dotenv import load_dotenv

import dspy

load_dotenv(override=True)

# Nexar API Credentials
NEXAR_CLIENT_ID = os.getenv("NEXAR_CLIENT_ID", "")
NEXAR_CLIENT_SECRET = os.getenv("NEXAR_CLIENT_SECRET", "")
_procurement_api_is_live_env = os.getenv("PROCUREMENT_API_IS_LIVE", "false").lower() == "true"
# Only enable "live" calls when credentials are present; otherwise the procurement
# tooling falls back to cached/mock behavior without preventing the API from booting.
PROCUREMENT_API_IS_LIVE = bool(_procurement_api_is_live_env and NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET)

# --- Xentral API Configuration ---
# Loaded from .env (gitignored) so secrets stay out of git.
XENTRAL_API_KEY = os.getenv("XENTRAL_API_KEY")
XENTRAL_BASE_URL = os.getenv("XENTRAL_BASE_URL", "https://kako.xentral.biz/api/v1")
XENTRAL_TIMEOUT_SECONDS = 10
XENTRAL_BEARER_TOKEN = os.getenv("XENTRAL_BEARER_TOKEN", XENTRAL_API_KEY or "")

# --- Supabase / Postgres configuration ---
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")

# --- Gemini model handles ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_3_PRO = dspy.LM("gemini/gemini-3-pro-preview", api_key=GOOGLE_API_KEY)
GEMINI_2_5_PRO = dspy.LM("gemini/gemini-2.5-pro", api_key=GOOGLE_API_KEY)
GEMINI_2_5_FLASH = dspy.LM("gemini/gemini-2.5-flash", api_key=GOOGLE_API_KEY)
GEMINI_2_5_FLASH_LITE = dspy.LM("gemini/gemini-2.5-flash-lite", api_key=GOOGLE_API_KEY)
