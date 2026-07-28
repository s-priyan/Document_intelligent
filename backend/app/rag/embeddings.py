"""HuggingFace embedding model provider (FR-5).

The model is loaded lazily and cached process-wide because loading
sentence-transformer weights is expensive and only needed at ingestion time.
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
