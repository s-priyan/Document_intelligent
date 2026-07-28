"""Business logic for creating, reading and listing knowledge indexes."""

import json
import re
import uuid
from datetime import datetime, timezone

from app.core.exceptions import IndexAlreadyExistsError, IndexNotFoundError
from app.schemas.knowledge_index import KnowledgeIndexResponse
from app.services.storage import StorageService

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Convert a display name into a filesystem-safe slug."""
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


class KnowledgeIndexService:
    """Create, read and list knowledge indexes backed by the filesystem."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def create(self, name: str) -> KnowledgeIndexResponse:
        """Create a new knowledge index folder and metadata file.

        :raises IndexAlreadyExistsError: if an index with the derived id exists.
        """
        index_id = slugify(name)
        if self._storage.index_exists(index_id):
            raise IndexAlreadyExistsError(f"Knowledge index '{index_id}' already exists.")
        return self._persist_index(index_id, name)

    def get_or_create(self, index_id: str) -> KnowledgeIndexResponse:
        """Return an existing index, or create it on first use if absent.

        Used by the upload flow so posting documents to an unknown index
        provisions it automatically (its id doubles as the display name).
        """
        if self._storage.index_exists(index_id):
            return self._to_response(self._read_meta(index_id))
        return self._persist_index(index_id, index_id)

    def _persist_index(self, index_id: str, name: str) -> KnowledgeIndexResponse:
        """Create the index folders and metadata file for the given id."""
        self._storage.create_index_dirs(index_id)
        meta = {
            "id": index_id,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._storage.meta_path(index_id).write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        return self._to_response(meta)

    def get(self, index_id: str) -> KnowledgeIndexResponse:
        """Return metadata for a single index.

        :raises IndexNotFoundError: if the index does not exist.
        """
        return self._to_response(self._read_meta(index_id))

    def list(self) -> list[KnowledgeIndexResponse]:
        """Return metadata for every knowledge index."""
        root = self._storage.root
        if not root.exists():
            return []
        return [
            self._to_response(self._read_meta(entry.name))
            for entry in sorted(root.iterdir())
            if entry.is_dir() and self._storage.index_exists(entry.name)
        ]

    def ensure_exists(self, index_id: str) -> None:
        """Verify an index exists before it is used.

        :raises IndexNotFoundError: if the index does not exist.
        """
        if not self._storage.index_exists(index_id):
            raise IndexNotFoundError(f"Knowledge index '{index_id}' not found.")

    def _read_meta(self, index_id: str) -> dict:
        """Load and return the metadata dict for an index.

        :raises IndexNotFoundError: if the index does not exist.
        """
        if not self._storage.index_exists(index_id):
            raise IndexNotFoundError(f"Knowledge index '{index_id}' not found.")
        return json.loads(self._storage.meta_path(index_id).read_text(encoding="utf-8"))

    def _to_response(self, meta: dict) -> KnowledgeIndexResponse:
        """Map a metadata dict to the API response model."""
        return KnowledgeIndexResponse(
            id=meta["id"],
            name=meta["name"],
            created_at=meta["created_at"],
            document_count=self._count_documents(meta["id"]),
        )

    def _count_documents(self, index_id: str) -> int:
        """Count the original files stored under an index."""
        raw_dir = self._storage.raw_dir(index_id)
        if not raw_dir.exists():
            return 0
        return sum(1 for path in raw_dir.iterdir() if path.is_file())
