"""Application configuration and shared settings."""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM = "gpt-5-2025-08-07"

# --- Xentral API Configuration ---
# Loaded from .env (gitignored) so secrets stay out of git.
XENTRAL_API_KEY = os.getenv("XENTRAL_API_KEY")
XENTRAL_BASE_URL = os.getenv("XENTRAL_BASE_URL", "https://kako.xentral.biz/api/v1")
