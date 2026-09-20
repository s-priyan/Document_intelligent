"""Question-answering endpoint over a knowledge index (FR-8 to FR-12)."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from app.api.deps import get_query_service
from app.schemas.query import QueryRequest, QueryResponse, QueryStreamEvent
from app.services.query_service import QueryService

router = APIRouter(prefix="/knowledge-indexes/{index_id}/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_knowledge_index(
    index_id: str,
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    """Answer a natural-language question grounded in the index's documents.

    Retrieves the most relevant chunks (FR-9), generates a grounded answer via a
    LangGraph + GPT pipeline (FR-10), returns citations for the sources used
    (FR-11), and declines to answer when no relevant context is found (FR-12).
    Supply ``session_id`` to continue a multi-turn conversation.
    """
    return service.answer(index_id, payload.question, payload.session_id)


@router.post("/stream")
def stream_knowledge_index_query(
    index_id: str,
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> EventSourceResponse:
    """Answer a question as a server-sent event stream.

    Emits ``session``, then ``citations``, then a ``delta`` per answer token,
    and finally ``done`` with the complete answer. A failure after the stream
    has opened arrives as a terminal ``error`` event instead of ``done``.
    """
    events = service.stream_answer(index_id, payload.question, payload.session_id)
    return EventSourceResponse(_as_server_sent_events(events))


async def _as_server_sent_events(
    events: AsyncIterator[QueryStreamEvent],
) -> AsyncIterator[ServerSentEvent]:
    """Publish each domain event under its SSE event name with a JSON payload."""
    async for event in events:
        yield ServerSentEvent(event=event.event, data=event.model_dump_json())
