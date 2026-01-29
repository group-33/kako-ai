from __future__ import annotations

from functools import lru_cache

try:
    from google import genai
except ImportError:
    genai = None

from backend.src.config import VERTEX_ARGS


@lru_cache(maxsize=1)
def _client():
    if genai is None:
        raise ImportError("The 'google' package is required for embeddings but not installed.")
    return genai.Client(
        vertexai=True,
        project=VERTEX_ARGS["project"],
        location=VERTEX_ARGS["vertex_location"],
    )


def get_vertex_embedding(text: str) -> list[float]:
    if not text:
        text = ""
    # Check client availability before trying to use it
    if genai is None:
        print("Warning: Google GenAI client not available. Skipping embedding.")
        return []
        
    try:
        client = _client()
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[text],
        )
        return list(response.embeddings[0].values)
    except Exception as e:
        print(f"Embedding error: {e}")
        return []
