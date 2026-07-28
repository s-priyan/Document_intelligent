"""Orchestrates question answering over a knowledge index (FR-8 to FR-12)."""

import logging
import uuid

from app.core.exceptions import AppError, QueryError
from app.rag.qa_graph import QaGraph
from app.schemas.query import QueryResponse
from app.services.knowledge_index_service import KnowledgeIndexService

logger = logging.getLogger(__name__)


class QueryService:
    """Validate the target index, run the RAG graph, and shape the response."""

    def __init__(self, index_service: KnowledgeIndexService, qa_graph: QaGraph) -> None:
        self._index_service = index_service
        self._qa_graph = qa_graph

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
