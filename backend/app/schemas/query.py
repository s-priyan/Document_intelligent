"""Pydantic models for question answering over a knowledge index (FR-8 to FR-12)."""

from typing import ClassVar

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
    speak: bool = Field(
        default=False,
        description="Stream spoken audio alongside the answer text (streaming endpoint only).",
    )


class QueryResponse(BaseModel):
    """A grounded answer with its citations and the (possibly new) session id."""

    answer: str
    citations: list[Citation]
    session_id: str


class QueryStreamEvent(BaseModel):
    """Base class for the events emitted by the streaming query endpoint.

    ``event`` is the SSE event name the payload is published under; the JSON
    body of the frame is the serialised model itself.
    """

    event: ClassVar[str]


class SessionEvent(QueryStreamEvent):
    """Announces the session id for the turn; always the first event sent."""

    event: ClassVar[str] = "session"

    session_id: str


class CitationsEvent(QueryStreamEvent):
    """The sources the answer will be grounded in, sent before any text (FR-11)."""

    event: ClassVar[str] = "citations"

    citations: list[Citation]


class DeltaEvent(QueryStreamEvent):
    """An incremental piece of the answer as the model produces it."""

    event: ClassVar[str] = "delta"

    text: str


class AudioEvent(QueryStreamEvent):
    """Spoken audio for one sentence of the answer, sent as the answer streams.

    Emitted only when the caller asked for speech. Audio trails the text it
    belongs to, so these are interleaved with (and may follow) the deltas.
    """

    event: ClassVar[str] = "audio"

    sequence: int
    text: str
    mime_type: str = "audio/wav"
    audio_base64: str


class DoneEvent(QueryStreamEvent):
    """Terminal success event carrying the concatenated answer."""

    event: ClassVar[str] = "done"

    answer: str


class ErrorEvent(QueryStreamEvent):
    """Terminal failure event; replaces :class:`DoneEvent` when a turn fails."""

    event: ClassVar[str] = "error"

    detail: str
