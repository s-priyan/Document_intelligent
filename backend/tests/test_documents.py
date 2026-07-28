"""Tests for knowledge-index and document ingestion endpoints (FR-1 to FR-5).

The ``.txt`` path exercises validation, storage, parsing and chunking without
requiring the heavy Docling backend or the embedding model (a fake vector store
stands in for Chroma).
"""

from app.core.config import Settings
from app.rag.chunking import DocumentChunker


def test_health(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_index(client) -> None:
    created = client.post("/api/knowledge-indexes", json={"name": "My Docs"})
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == "my-docs"
    assert body["document_count"] == 0

    listed = client.get("/api/knowledge-indexes").json()
    assert any(item["id"] == "my-docs" for item in listed)


def test_duplicate_index_returns_conflict(client) -> None:
    client.post("/api/knowledge-indexes", json={"name": "Dup"})
    response = client.post("/api/knowledge-indexes", json={"name": "Dup"})
    assert response.status_code == 409


def test_upload_to_missing_index_auto_creates_it(client) -> None:
    response = client.post(
        "/api/knowledge-indexes/auto/documents",
        files=[("files", ("a.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 200
    assert response.json()["ingested"] == 1

    # The index now exists and is listed for selection.
    index = client.get("/api/knowledge-indexes/auto").json()
    assert index["id"] == "auto"
    assert index["document_count"] == 1


def test_bulk_upload_validates_parses_and_indexes(client, vector_store) -> None:
    client.post("/api/knowledge-indexes", json={"name": "Batch"})
    response = client.post(
        "/api/knowledge-indexes/batch/documents",
        files=[
            ("files", ("good.txt", b"hello world", "text/plain")),
            ("files", ("bad.exe", b"MZ", "application/octet-stream")),
            ("files", ("empty.txt", b"", "text/plain")),
        ],
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["ingested"], body["failed"]) == (3, 1, 2)

    statuses = {result["filename"]: result["status"] for result in body["results"]}
    assert statuses == {"good.txt": "ingested", "bad.exe": "failed", "empty.txt": "failed"}

    good = next(r for r in body["results"] if r["filename"] == "good.txt")
    assert good["chunk_count"] == 1

    # The successfully ingested file is now counted against the index...
    index = client.get("/api/knowledge-indexes/batch").json()
    assert index["document_count"] == 1
    # ...and its chunk was embedded/stored (FR-5) with source metadata.
    stored = vector_store.added["batch"]
    assert len(stored) == 1
    assert stored[0].metadata["source"] == "good.txt"
    assert stored[0].metadata["chunk_index"] == 0


def test_chunker_splits_long_text_with_overlap() -> None:
    settings = Settings(chunk_size=100, chunk_overlap=20)
    chunker = DocumentChunker(settings)

    chunks = chunker.chunk("word " * 200, {"source": "big.txt"})

    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "big.txt" for chunk in chunks)
    assert all("start_index" in chunk.metadata for chunk in chunks)
