"""
Local LLM configuration for APEX-AI.

No cloud APIs are used.
The model runs through Ollama on the local machine.
"""

import os
from functools import lru_cache

from langchain_ollama import ChatOllama


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5vl:7b"
)


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    """
    Return a singleton local LLM instance.

    Keeping one instance avoids repeatedly initializing
    the model configuration during an analysis.
    """

    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
        num_ctx=8192,
    )


def get_model_info() -> dict:
    """
    Return model information for the UI / health checks.
    """

    return {
        "provider": "Ollama",
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL,
        "local": True,
        "cloud_api": False,
    }