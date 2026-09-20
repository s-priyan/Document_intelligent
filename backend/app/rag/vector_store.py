"""Per-index Chroma vector store persistence (FR-5).

Each knowledge index owns an isolated, on-disk Chroma collection under
``storage/{index_id}/chroma/``. A constant collection name is used because the
persist directory already scopes the data to a single index.
"""

import threading
from typing import TYPE_CHECKING

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.services.storage import StorageService

if TYPE_CHECKING:
    from langchain_chroma import Chroma

_COLLECTION_NAME = "documents"


class VectorStoreService:
    """Create and populate a Chroma store scoped to a single knowledge index."""

    def __init__(self, storage: StorageService, embeddings: Embeddings) -> None:
        self._storage = storage
        self._embeddings = embeddings
        self._stores: dict[str, "Chroma"] = {}
        self._lock = threading.Lock()

    def add_documents(
        self, index_id: str, documents: list[Document], ids: list[str]
    ) -> None:
        """Embed and persist chunk documents into the index's Chroma collection."""
        self._open(index_id).add_documents(documents=documents, ids=ids)

    def search(self, index_id: str, query: str, k: int) -> list[Document]:
        """Return the ``k`` chunks most similar to ``query`` for an index (FR-9)."""
        return self._open(index_id).similarity_search(query, k=k)

    def _open(self, index_id: str) -> "Chroma":
        """Return the index's Chroma store, opening it on first use.

        Opening a persistent collection costs roughly a second, so each store is
        kept for the process lifetime instead of being rebuilt per request. The
        lock keeps concurrent requests for the same index from opening it twice.
        """
        with self._lock:
            if index_id not in self._stores:
                self._stores[index_id] = self._create(index_id)
            return self._stores[index_id]

    def _create(self, index_id: str) -> "Chroma":
        """Build the Chroma store for an index, creating its folder if absent."""
        from langchain_chroma import Chroma

        persist_dir = self._storage.chroma_dir(index_id)
        persist_dir.mkdir(parents=True, exist_ok=True)
        return Chroma(
            collection_name=_COLLECTION_NAME,
            embedding_function=self._embeddings,
            persist_directory=str(persist_dir),
        )
