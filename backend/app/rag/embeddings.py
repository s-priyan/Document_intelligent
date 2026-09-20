"""HuggingFace embedding model provider (FR-5).

Loading sentence-transformer weights is expensive, so the model is cached
process-wide and normally constructed once during application startup
(see ``app.main.lifespan``), falling back to first use if that is disabled.
"""

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.core.config import get_settings


@lru_cache
def get_embeddings() -> Embeddings:
    """Build the ``BAAI/bge-small-en-v1.5`` embeddings, loaded once.

    Vectors are L2-normalized so cosine similarity can be used for retrieval.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=get_settings().embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
