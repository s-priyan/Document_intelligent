"""Pydantic models for knowledge-index endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateKnowledgeIndexRequest(BaseModel):
    """Request body for creating a knowledge index."""

    name: str = Field(min_length=1, max_length=100, description="Human-readable index name.")


class KnowledgeIndexResponse(BaseModel):
    """Metadata describing a knowledge index."""

    id: str
    name: str
    created_at: datetime
    document_count: int
