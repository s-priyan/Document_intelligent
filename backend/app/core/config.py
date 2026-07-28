"""Application configuration loaded from environment variables and ``.env``."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend service."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "Chat With Your Docs API"
    api_prefix: str = "/api"

    # Where uploaded materials and parsed artifacts are stored.
    storage_dir: Path = Path("storage")

    # Upload validation (FR-2).
    max_file_size_mb: int = 100
    allowed_extensions: set[str] = {".pdf", ".docx", ".txt", ".md"}

    # Chunking (FR-4).
    chunk_size: int = 5000
    chunk_overlap: int = 150

    # Embedding & indexing (FR-5).
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Question answering / RAG generation (FR-8 to FR-12).
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"
    retrieval_k: int = 4

    cors_origins: list[str] = ["http://localhost:3000","http://localhost:3001","http://localhost:3002"]

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum allowed upload size expressed in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()
