"""Pydantic models for question answering over a knowledge index (FR-8 to FR-12)."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A reference to the source location a piece of an answer is grounded in (FR-11)."""

    source: str
    section: str | None = None
    start_index: int | None = None
    snippet: str | None = None


class QueryRequest(BaseModel):
    """A natural-language question, optionally continuing an existing session (FR-8)."""

    question: str = Field(..., min_length=1, description="The user's natural-language question.")
    session_id: str | None = Field(
        default=None,
        description="Conversation id to continue a multi-turn session; omit to start a new one.",
    )


class QueryResponse(BaseModel):
    """A grounded answer with its citations and the (possibly new) session id."""

    answer: str
    citations: list[Citation]
    session_id: str
