from __future__ import annotations

from functools import lru_cache

from google import genai

from backend.src.config import VERTEX_ARGS


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=VERTEX_ARGS["project"],
        location=VERTEX_ARGS["vertex_location"],
    )


def get_vertex_embedding(text: str) -> list[float]:
    if not text:
        text = ""
    client = _client()
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[text],
    )
    return list(response.embeddings[0].values)
