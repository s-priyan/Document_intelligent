"""Pydantic models for document upload and ingestion (FR-1 to FR-3)."""

from enum import Enum

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    """Per-file ingestion outcome."""

    INGESTED = "ingested"
    FAILED = "failed"


class DocumentResult(BaseModel):
    """Result of processing a single uploaded document."""

    filename: str
    status: DocumentStatus
    size_bytes: int | None = None
    stored_path: str | None = None
    parsed_path: str | None = None
    chunk_count: int | None = None
    error: str | None = None


class BulkUploadResponse(BaseModel):
    """Aggregate result of a bulk upload request."""

    index_id: str
    total: int
    ingested: int
    failed: int
    results: list[DocumentResult]
