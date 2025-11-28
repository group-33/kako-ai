"""Application configuration and shared settings."""
import os
from dotenv import load_dotenv

import dspy

load_dotenv(override=True)

# LLM = "gpt-5-2025-08-07"

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
