import os
import requests
from typing import List
from backend.nim_guardrails import load_nim_settings, call_with_nim_limits


def get_embedding(text: str, is_query: bool = True) -> List[float]:
    """
    Retrieves the embedding vector from the NVIDIA NIM embeddings API.
    Handles rate-limiting and API pacing using call_with_nim_limits.
    """
    nim_settings = load_nim_settings()

    # Default to the optimized question-answering retrieval model
    model = os.getenv("NVIDIA_NIM_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5").strip()

    if not nim_settings.api_key:
        raise ValueError("NVIDIA_NIM_API_KEY is not configured in environment variables.")

    def _call():
        headers = {
            "Authorization": f"Bearer {nim_settings.api_key}",
            "Content-Type": "application/json",
        }
        # Specify input_type as "query" or "passage" as required by NIM retriever embeddings models
        input_type = "query" if is_query else "passage"
        payload = {
            "model": model,
            "input": [text],
            "input_type": input_type,
            "encoding_format": "float",
        }
        url = f"{nim_settings.base_url.rstrip('/')}/embeddings"
        response = requests.post(
            url, json=payload, headers=headers, timeout=nim_settings.timeout_seconds
        )
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        raise RuntimeError(
            f"NVIDIA NIM embeddings API failed (status {response.status_code}): {response.text}"
        )

    return call_with_nim_limits(_call, nim_settings)
