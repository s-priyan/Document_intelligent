"""Shared pytest fixtures wiring the app to an isolated temp storage directory."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.api import deps
from app.core.config import Settings
from app.ingestion.parser import DocumentParser
from app.ingestion.validator import UploadValidator
from app.main import app
from app.rag.chunking import DocumentChunker
from app.rag.indexer import DocumentIndexer
from app.services.knowledge_index_service import KnowledgeIndexService
from app.services.storage import StorageService


class FakeVectorStore:
    """In-memory stand-in for the Chroma-backed store (no embedding model).

    Lets tests exercise the real chunker and indexer without downloading the
    HuggingFace embedding weights or spinning up Chroma.
    """

    def __init__(self) -> None:
        self.added: dict[str, list[Document]] = {}

    def add_documents(self, index_id: str, documents: list[Document], ids: list[str]) -> None:
        self.added.setdefault(index_id, []).extend(documents)


@pytest.fixture
def vector_store() -> FakeVectorStore:
    """Expose the fake vector store so tests can assert what was indexed."""
    return FakeVectorStore()


@pytest.fixture
def client(tmp_path, vector_store: FakeVectorStore) -> Iterator[TestClient]:
    """Provide a TestClient backed by services pointed at a temp storage dir."""
    settings = Settings(storage_dir=tmp_path / "storage")
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    storage = StorageService(settings)
    index_service = KnowledgeIndexService(storage)
    indexer = DocumentIndexer(DocumentChunker(settings), vector_store)

    app.dependency_overrides[deps.get_storage_service] = lambda: storage
    app.dependency_overrides[deps.get_knowledge_index_service] = lambda: index_service
    app.dependency_overrides[deps.get_upload_validator] = lambda: UploadValidator(settings)
    app.dependency_overrides[deps.get_document_parser] = lambda: DocumentParser()
    app.dependency_overrides[deps.get_document_indexer] = lambda: indexer

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
