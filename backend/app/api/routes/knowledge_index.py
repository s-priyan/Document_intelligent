"""Knowledge-index endpoints: create, list and retrieve."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_knowledge_index_service
from app.schemas.knowledge_index import CreateKnowledgeIndexRequest, KnowledgeIndexResponse
from app.services.knowledge_index_service import KnowledgeIndexService

router = APIRouter(prefix="/knowledge-indexes", tags=["knowledge-indexes"])


@router.post("", response_model=KnowledgeIndexResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_index(
    payload: CreateKnowledgeIndexRequest,
    service: KnowledgeIndexService = Depends(get_knowledge_index_service),
) -> KnowledgeIndexResponse:
    """Create a new, named knowledge index."""
    return service.create(payload.name)


@router.get("", response_model=list[KnowledgeIndexResponse])
def list_knowledge_indexes(
    service: KnowledgeIndexService = Depends(get_knowledge_index_service),
) -> list[KnowledgeIndexResponse]:
    """List all knowledge indexes available to select for a chat session."""
    return service.list()


@router.get("/{index_id}", response_model=KnowledgeIndexResponse)
def get_knowledge_index(
    index_id: str,
    service: KnowledgeIndexService = Depends(get_knowledge_index_service),
) -> KnowledgeIndexResponse:
    """Retrieve a single knowledge index by its id."""
    return service.get(index_id)
