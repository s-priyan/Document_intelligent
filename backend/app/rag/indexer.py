"""Chunk-and-index orchestration bridging parsing and the vector store (FR-4/FR-5)."""

from app.core.exceptions import IndexingError
from app.rag.chunking import DocumentChunker
from app.rag.vector_store import VectorStoreService


class DocumentIndexer:
    """Chunk parsed text and store the resulting embeddings for an index."""

    def __init__(self, chunker: DocumentChunker, vector_store: VectorStoreService) -> None:
        self._chunker = chunker
        self._vector_store = vector_store

    def index(self, index_id: str, text: str, source: str) -> int:
        """Chunk ``text`` from ``source`` and add its embeddings to the index.

        :returns: the number of chunks stored.
        :raises IndexingError: if chunking, embedding or storage fails.
        """
        try:
            chunks = self._chunker.chunk(text, {"index_id": index_id, "source": source})
            if not chunks:
                return 0
            for position, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = position
            ids = [f"{source}::{position}" for position in range(len(chunks))]
            self._vector_store.add_documents(index_id, chunks, ids)
            return len(chunks)
        except IndexingError:
            raise
        except Exception as exc:  # embedding / vector-store backend failures
            raise IndexingError(f"Failed to index '{source}': {exc}") from exc
