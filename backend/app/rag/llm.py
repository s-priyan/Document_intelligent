"""OpenAI chat model provider for grounded answer generation (FR-10).

The client is created lazily and cached process-wide. The API key is read from
settings; when unset, ``ChatOpenAI`` falls back to the ``OPENAI_API_KEY``
environment variable.
"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    """Build the configured OpenAI chat model, created once.

    ``temperature`` is intentionally left at the model default so newer models
    that reject non-default values are supported; grounding is enforced via the
    system prompt rather than sampling settings.
    """
    settings = get_settings()
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key or None)
