"""Per-index Chroma vector store persistence (FR-5).

Each knowledge index owns an isolated, on-disk Chroma collection under
``storage/{index_id}/chroma/``. A constant collection name is used because the
persist directory already scopes the data to a single index.
"""

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.services.storage import StorageService

_COLLECTION_NAME = "documents"


class VectorStoreService:
    """Create and populate a Chroma store scoped to a single knowledge index."""

    def __init__(self, storage: StorageService, embeddings: Embeddings) -> None:
        self._storage = storage
        self._embeddings = embeddings

    def add_documents(
        self, index_id: str, documents: list[Document], ids: list[str]
    ) -> None:
        """Embed and persist chunk documents into the index's Chroma collection."""
        self._open(index_id).add_documents(documents=documents, ids=ids)

    def search(self, index_id: str, query: str, k: int) -> list[Document]:
        """Return the ``k`` chunks most similar to ``query`` for an index (FR-9)."""
        return self._open(index_id).similarity_search(query, k=k)

    def _open(self, index_id: str):
        """Open (creating if needed) the Chroma store for an index."""
        from langchain_chroma import Chroma

        persist_dir = self._storage.chroma_dir(index_id)
        persist_dir.mkdir(parents=True, exist_ok=True)
        return Chroma(
            collection_name=_COLLECTION_NAME,
            embedding_function=self._embeddings,
            persist_directory=str(persist_dir),
        )
