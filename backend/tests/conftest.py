"""Shared pytest fixtures wiring the app to an isolated temp storage directory."""

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.api import deps
from app.core.config import Settings, get_settings
from app.ingestion.parser import DocumentParser
from app.ingestion.validator import UploadValidator
from app.main import app
from app.rag.chunking import DocumentChunker
from app.rag.indexer import DocumentIndexer
from app.schemas.query import (
    Citation,
    CitationsEvent,
    DeltaEvent,
    DoneEvent,
    QueryStreamEvent,
)
from app.services.knowledge_index_service import KnowledgeIndexService
from app.services.query_service import QueryService
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


class FakeQaGraph:
    """Scripted stand-in for the LangGraph RAG pipeline (no LLM, no embeddings).

    ``deltas`` are the answer pieces to emit; setting ``failure`` makes the turn
    blow up after the citations have been sent, which is the interesting case
    for a stream whose HTTP status is already committed.
    """

    def __init__(self) -> None:
        self.deltas = ["Hello", " world"]
        self.citations = [Citation(source="a.txt", snippet="hello world")]
        self.failure: Exception | None = None
        self.calls: list[tuple[str, str, str]] = []

    def answer(
        self, index_id: str, question: str, thread_id: str
    ) -> tuple[str, list[Citation]]:
        self.calls.append((index_id, question, thread_id))
        if self.failure is not None:
            raise self.failure
        return "".join(self.deltas), self.citations

    async def astream_answer(
        self, index_id: str, question: str, thread_id: str
    ) -> AsyncIterator[QueryStreamEvent]:
        self.calls.append((index_id, question, thread_id))
        yield CitationsEvent(citations=self.citations)
        for delta in self.deltas:
            if self.failure is not None:
                raise self.failure
            yield DeltaEvent(text=delta)
        yield DoneEvent(answer="".join(self.deltas))


@pytest.fixture
def vector_store() -> FakeVectorStore:
    """Expose the fake vector store so tests can assert what was indexed."""
    return FakeVectorStore()


@pytest.fixture
def qa_graph() -> FakeQaGraph:
    """Expose the scripted QA graph so tests can control the answer stream."""
    return FakeQaGraph()


@pytest.fixture
def client(
    tmp_path, monkeypatch, vector_store: FakeVectorStore, qa_graph: FakeQaGraph
) -> Iterator[TestClient]:
    """Provide a TestClient backed by services pointed at a temp storage dir."""
    settings = Settings(storage_dir=tmp_path / "storage")
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    # Entering the TestClient runs the lifespan, which would otherwise load the
    # real embedding weights the fakes above exist to avoid.
    monkeypatch.setattr(get_settings(), "warm_embeddings_on_startup", False)

    storage = StorageService(settings)
    index_service = KnowledgeIndexService(storage)
    indexer = DocumentIndexer(DocumentChunker(settings), vector_store)

    app.dependency_overrides[deps.get_storage_service] = lambda: storage
    app.dependency_overrides[deps.get_knowledge_index_service] = lambda: index_service
    app.dependency_overrides[deps.get_upload_validator] = lambda: UploadValidator(settings)
    app.dependency_overrides[deps.get_document_parser] = lambda: DocumentParser()
    app.dependency_overrides[deps.get_document_indexer] = lambda: indexer
    app.dependency_overrides[deps.get_query_service] = lambda: QueryService(
        index_service, qa_graph
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
