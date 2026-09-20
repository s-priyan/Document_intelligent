"""Tests for the per-index Chroma store wrapper (FR-5).

Stub embeddings stand in for the HuggingFace model so a real Chroma collection
can be exercised without loading any weights.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.rag.vector_store import VectorStoreService
from app.services.storage import StorageService


class StubEmbeddings(Embeddings):
    """Deterministic, weight-free embeddings so Chroma can index and search."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), float(text.count("e")), 1.0]


def _service(tmp_path: Path) -> VectorStoreService:
    """Build a service pointed at an isolated storage directory."""
    settings = Settings(storage_dir=tmp_path / "storage")
    return VectorStoreService(StorageService(settings), StubEmbeddings())


def test_store_is_built_once_per_index(tmp_path, monkeypatch) -> None:
    opened: list[str] = []

    class CountingChroma:
        def __init__(self, *, collection_name, embedding_function, persist_directory) -> None:
            opened.append(persist_directory)

        def similarity_search(self, query: str, k: int) -> list[Document]:
            return []

    monkeypatch.setattr("langchain_chroma.Chroma", CountingChroma)
    service = _service(tmp_path)

    service.search("docs", "first question", 2)
    service.search("docs", "second question", 2)
    service.search("other", "third question", 2)

    assert len(opened) == 2


def test_added_documents_are_searchable(tmp_path) -> None:
    service = _service(tmp_path)
    service.add_documents(
        "docs",
        [Document(page_content="refunds take five days", metadata={"source": "a.txt"})],
        ["a-0"],
    )

    results = service.search("docs", "refunds take five days", 1)

    assert len(results) == 1
    assert results[0].metadata["source"] == "a.txt"
