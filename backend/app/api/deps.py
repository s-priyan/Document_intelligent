"""FastAPI dependency providers wiring services together (composition root)."""

from functools import lru_cache

from app.core.config import get_settings
from app.ingestion.parser import DocumentParser
from app.ingestion.validator import UploadValidator
from app.rag.chunking import DocumentChunker
from app.rag.citations import CitationBuilder
from app.rag.embeddings import get_embeddings
from app.rag.indexer import DocumentIndexer
from app.rag.llm import get_chat_model
from app.rag.qa_graph import QaGraph
from app.rag.vector_store import VectorStoreService
from app.services.knowledge_index_service import KnowledgeIndexService
from app.services.query_service import QueryService
from app.services.storage import StorageService


@lru_cache
def get_storage_service() -> StorageService:
    """Provide a singleton :class:`StorageService`."""
    return StorageService(get_settings())


@lru_cache
def get_knowledge_index_service() -> KnowledgeIndexService:
    """Provide a singleton :class:`KnowledgeIndexService`."""
    return KnowledgeIndexService(get_storage_service())


@lru_cache
def get_upload_validator() -> UploadValidator:
    """Provide a singleton :class:`UploadValidator`."""
    return UploadValidator(get_settings())


@lru_cache
def get_document_parser() -> DocumentParser:
    """Provide a singleton :class:`DocumentParser`."""
    return DocumentParser()


@lru_cache
def get_document_chunker() -> DocumentChunker:
    """Provide a singleton :class:`DocumentChunker` (FR-4)."""
    return DocumentChunker(get_settings())


@lru_cache
def get_vector_store_service() -> VectorStoreService:
    """Provide a singleton :class:`VectorStoreService` (FR-5)."""
    return VectorStoreService(get_storage_service(), get_embeddings())


@lru_cache
def get_document_indexer() -> DocumentIndexer:
    """Provide a singleton :class:`DocumentIndexer` (FR-4/FR-5)."""
    return DocumentIndexer(get_document_chunker(), get_vector_store_service())


@lru_cache
def get_citation_builder() -> CitationBuilder:
    """Provide a singleton :class:`CitationBuilder` (FR-11)."""
    return CitationBuilder(get_storage_service())


@lru_cache
def get_qa_graph() -> QaGraph:
    """Provide a singleton, compiled :class:`QaGraph` (FR-9/FR-10/FR-12).

    Compiling once keeps the in-memory checkpointer alive across requests so
    conversation history persists per session for the process lifetime.
    """
    return QaGraph(
        vector_store=get_vector_store_service(),
        citation_builder=get_citation_builder(),
        chat_model=get_chat_model(),
        retrieval_k=get_settings().retrieval_k,
    )


@lru_cache
def get_query_service() -> QueryService:
    """Provide a singleton :class:`QueryService` (FR-8)."""
    return QueryService(get_knowledge_index_service(), get_qa_graph())
