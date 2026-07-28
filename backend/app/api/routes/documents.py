"""Document ingestion endpoints: bulk upload (FR-1), validate (FR-2), parse (FR-3)."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import (
    get_document_indexer,
    get_document_parser,
    get_knowledge_index_service,
    get_storage_service,
    get_upload_validator,
)
from app.core.exceptions import AppError
from app.ingestion.parser import DocumentParser
from app.ingestion.validator import UploadValidator
from app.rag.indexer import DocumentIndexer
from app.schemas.documents import BulkUploadResponse, DocumentResult, DocumentStatus
from app.services.knowledge_index_service import KnowledgeIndexService
from app.services.storage import StorageService

router = APIRouter(prefix="/knowledge-indexes/{index_id}/documents", tags=["documents"])


@router.post("", response_model=BulkUploadResponse)
async def bulk_upload_documents(
    index_id: str,
    files: list[UploadFile] = File(..., description="One or more documents to ingest."),
    index_service: KnowledgeIndexService = Depends(get_knowledge_index_service),
    validator: UploadValidator = Depends(get_upload_validator),
    storage: StorageService = Depends(get_storage_service),
    parser: DocumentParser = Depends(get_document_parser),
    indexer: DocumentIndexer = Depends(get_document_indexer),
) -> BulkUploadResponse:
    """Bulk-upload documents into a knowledge index.

    Each file is validated (FR-2), stored in the index ``raw/`` folder (FR-1),
    parsed with Docling into ``parsed/`` (FR-3), then chunked (FR-4) and embedded
    into the index's Chroma store (FR-5). A per-file failure is reported in the
    response and does not abort the rest of the batch.

    The target index is created on first use if it does not already exist.
    """
    index_service.get_or_create(index_id)

    results = [
        await _process_single_upload(index_id, upload, validator, storage, parser, indexer)
        for upload in files
    ]
    ingested = sum(1 for result in results if result.status is DocumentStatus.INGESTED)
    return BulkUploadResponse(
        index_id=index_id,
        total=len(results),
        ingested=ingested,
        failed=len(results) - ingested,
        results=results,
    )


async def _process_single_upload(
    index_id: str,
    upload: UploadFile,
    validator: UploadValidator,
    storage: StorageService,
    parser: DocumentParser,
    indexer: DocumentIndexer,
) -> DocumentResult:
    """Validate, store, parse and index one uploaded file; captures errors per file."""
    filename = upload.filename or "unnamed"
    try:
        data = await upload.read()
        validator.validate(filename, len(data))
        stored_path = storage.save_raw_file(index_id, filename, data)
        markdown = parser.parse(stored_path)
        parsed_path = storage.save_parsed_markdown(index_id, stored_path.name, markdown)
        chunk_count = indexer.index(index_id, markdown, stored_path.name)
        return DocumentResult(
            filename=filename,
            status=DocumentStatus.INGESTED,
            size_bytes=len(data),
            stored_path=str(stored_path),
            parsed_path=str(parsed_path),
            chunk_count=chunk_count,
        )
    except AppError as exc:
        return DocumentResult(filename=filename, status=DocumentStatus.FAILED, error=exc.message)
    finally:
        await upload.close()
