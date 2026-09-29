"""Orchestrates question answering over a knowledge index (FR-8 to FR-12)."""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator

from app.core.exceptions import AppError, QueryError
from app.rag.qa_graph import QaGraph
from app.schemas.query import (
    ErrorEvent,
    QueryResponse,
    QueryStreamEvent,
    SessionEvent,
)
from app.services.knowledge_index_service import KnowledgeIndexService
from app.services.speech_stream import SpokenAnswerStream

logger = logging.getLogger(__name__)


class QueryService:
    """Validate the target index, run the RAG graph, and shape the response."""

    def __init__(
        self,
        index_service: KnowledgeIndexService,
        qa_graph: QaGraph,
        spoken_stream: SpokenAnswerStream | None = None,
    ) -> None:
        self._index_service = index_service
        self._qa_graph = qa_graph
        self._spoken_stream = spoken_stream

    def answer(self, index_id: str, question: str, session_id: str | None) -> QueryResponse:
        """Answer ``question`` against ``index_id`` within a conversation session.

        A new ``session_id`` is generated when none is supplied so the caller can
        continue the multi-turn conversation on subsequent requests.

        :raises IndexNotFoundError: if the knowledge index does not exist.
        :raises QueryError: if retrieval or answer generation fails.
        """
        self._index_service.ensure_exists(index_id)
        thread_id = session_id or uuid.uuid4().hex
        logger.info(
            "Query received | index=%s session=%s question=%r", index_id, thread_id, question
        )
        try:
            answer, citations = self._qa_graph.answer(index_id, question, thread_id)
        except AppError:
            logger.warning("Query rejected | index=%s session=%s", index_id, thread_id)
            raise
        # Domain errors already carry an HTTP status, so let them propagate.
        except Exception as exc:  # retrieval / LLM backend failures
            logger.exception("Query failed | index=%s session=%s", index_id, thread_id)
            raise QueryError(f"Failed to answer question: {exc}") from exc

        logger.info(
            "Query answered | index=%s session=%s citations=%d answer_chars=%d",
            index_id,
            thread_id,
            len(citations),
            len(answer),
        )
        return QueryResponse(answer=answer, citations=citations, session_id=thread_id)

    def stream_answer(
        self, index_id: str, question: str, session_id: str | None, speak: bool = False
    ) -> AsyncIterator[QueryStreamEvent]:
        """Answer ``question`` as a stream of events for server-sent delivery.

        The index is validated eagerly so a missing index still surfaces as a
        regular HTTP error, before any event has been written to the response.

        :param speak: Also emit an audio event per sentence; ignored when no
            speech engine is configured.
        :raises IndexNotFoundError: if the knowledge index does not exist.
        """
        self._index_service.ensure_exists(index_id)
        thread_id = session_id or uuid.uuid4().hex
        logger.info(
            "Query stream started | index=%s session=%s speak=%s question=%r",
            index_id,
            thread_id,
            speak,
            question,
        )
        events = self._stream_events(index_id, question, thread_id)
        if speak and self._spoken_stream is not None:
            return self._spoken_stream.stream(events)
        # Unrequested or unconfigured speech leaves the text stream untouched.

        return events

    async def _stream_events(
        self, index_id: str, question: str, thread_id: str
    ) -> AsyncIterator[QueryStreamEvent]:
        """Emit the session id, then the graph's events, degrading to an error event.

        Once streaming has begun the response status is already committed, so
        failures can only be reported in-band as an ``error`` event.
        """
        yield SessionEvent(session_id=thread_id)
        try:
            async for event in self._qa_graph.astream_answer(index_id, question, thread_id):
                yield event
        except asyncio.CancelledError:
            logger.info("Query stream cancelled | index=%s session=%s", index_id, thread_id)
            raise
        # Client disconnects cancel the task; propagate so the turn is abandoned.
        except AppError as exc:
            logger.warning("Query stream rejected | index=%s session=%s", index_id, thread_id)
            yield ErrorEvent(detail=exc.message)
        except Exception as exc:  # retrieval / LLM backend failures
            logger.exception("Query stream failed | index=%s session=%s", index_id, thread_id)
            yield ErrorEvent(detail=f"Failed to answer question: {exc}")
        else:
            logger.info("Query stream completed | index=%s session=%s", index_id, thread_id)
