"""Question-answering endpoint over a knowledge index (FR-8 to FR-12)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_query_service
from app.schemas.query import QueryRequest, QueryResponse
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
