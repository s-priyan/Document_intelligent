"""Filesystem storage for knowledge indexes and their documents.

Layout (one flat folder per index):

    storage/{index_id}/
        meta.json      # index metadata
        raw/           # original uploaded files
        parsed/        # Docling-extracted markdown
"""

from pathlib import Path

from app.core.config import Settings


class StorageService:
    """Resolve and create on-disk paths for knowledge indexes and documents."""

    def __init__(self, settings: Settings) -> None:
        self._root = settings.storage_dir

    @property
    def root(self) -> Path:
        """Root directory containing all knowledge indexes."""
        return self._root

    def index_dir(self, index_id: str) -> Path:
        """Return the folder for a single index."""
        return self._root / index_id

    def raw_dir(self, index_id: str) -> Path:
        """Return the folder holding original uploaded files for an index."""
        return self.index_dir(index_id) / "raw"

    def parsed_dir(self, index_id: str) -> Path:
        """Return the folder holding parsed markdown for an index."""
        return self.index_dir(index_id) / "parsed"

    def chroma_dir(self, index_id: str) -> Path:
        """Return the folder holding the index's Chroma vector store (FR-5)."""
        return self.index_dir(index_id) / "chroma"

    def meta_path(self, index_id: str) -> Path:
        """Return the metadata file path for an index."""
        return self.index_dir(index_id) / "meta.json"

    def create_index_dirs(self, index_id: str) -> None:
        """Create the ``raw/`` and ``parsed/`` subfolders for a new index."""
        self.raw_dir(index_id).mkdir(parents=True, exist_ok=True)
        self.parsed_dir(index_id).mkdir(parents=True, exist_ok=True)

    def index_exists(self, index_id: str) -> bool:
        """Return whether an index (its metadata file) exists."""
        return self.meta_path(index_id).exists()

    def save_raw_file(self, index_id: str, filename: str, data: bytes) -> Path:
        """Persist an uploaded file into the index ``raw/`` folder.

        A numeric suffix is appended when a file with the same name already
        exists, so uploads never silently overwrite earlier ones.
        """
        raw_dir = self.raw_dir(index_id)
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = self._unique_path(raw_dir / filename)
        target.write_bytes(data)
        return target

    def save_parsed_markdown(self, index_id: str, stored_filename: str, markdown: str) -> Path:
        """Persist Docling-extracted markdown under the index ``parsed/`` folder."""
        parsed_dir = self.parsed_dir(index_id)
        parsed_dir.mkdir(parents=True, exist_ok=True)
        target = (parsed_dir / stored_filename).with_suffix(".md")
        target.write_text(markdown, encoding="utf-8")
        return target

    @staticmethod
    def _unique_path(path: Path) -> Path:
        """Return ``path`` or a non-clashing variant like ``name_1.pdf``."""
        if not path.exists():
            return path
        # Filename already taken, so append an incrementing suffix.
        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
