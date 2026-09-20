"""Build answer citations from retrieved chunks (FR-11).

Each citation names the source document, its location, and the grounding
chunk's text. The location is a markdown ``section`` (the nearest heading at or
above the chunk) plus the chunk's character ``start_index``. Sections are
derived at query time from the persisted parsed markdown, so no ingestion
changes are required.

Citations mirror retrieval one-to-one: every chunk the model was given is
surfaced, so the reader sees exactly the evidence the answer was built on.
"""

import re
from pathlib import Path

from langchain_core.documents import Document

from app.schemas.query import Citation
from app.services.storage import StorageService

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


class CitationBuilder:
    """Map retrieved chunks to source/section citations."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def build(self, documents: list[Document]) -> list[Citation]:
        """Return one citation per retrieved chunk in ``documents``."""
        parsed_cache: dict[tuple[str, str], str | None] = {}
        citations: list[Citation] = []
        for document in documents:
            metadata = document.metadata
            source = metadata.get("source", "unknown")
            index_id = metadata.get("index_id", "")
            start_index = metadata.get("start_index")
            citations.append(
                Citation(
                    source=source,
                    section=self._section_for(index_id, source, start_index, parsed_cache),
                    start_index=start_index,
                    snippet=self._snippet(document.page_content),
                )
            )
        return citations

    @staticmethod
    def _snippet(text: str) -> str | None:
        """Return the chunk ``text`` as shown to the model, trimmed at the edges.

        The chunker already bounds this to ``chunk_size``, so no further cap is
        applied; line breaks are kept so the excerpt reads as it does in the
        source document.
        """
        excerpt = text.strip()
        return excerpt or None
        # Empty chunks carry no useful excerpt.

    def _section_for(
        self,
        index_id: str,
        source: str,
        start_index: int | None,
        parsed_cache: dict[tuple[str, str], str | None],
    ) -> str | None:
        """Return the nearest markdown heading at or above ``start_index``."""
        if start_index is None:
            return None
        # No offset, so no section can be located.

        text = self._parsed_text(index_id, source, parsed_cache)
        if text is None:
            return None
        # Parsed markdown missing, so the section is unknown.

        section: str | None = None
        for match in _HEADING_RE.finditer(text):
            if match.start() > start_index:
                break
            # Later headings are past the chunk, so stop scanning.

            section = match.group(1).strip()
        return section

    def _parsed_text(
        self, index_id: str, source: str, parsed_cache: dict[tuple[str, str], str | None]
    ) -> str | None:
        """Read (and cache) the parsed markdown backing a source document."""
        cache_key = (index_id, source)
        if cache_key in parsed_cache:
            return parsed_cache[cache_key]

        path = (self._storage.parsed_dir(index_id) / source).with_suffix(".md")
        text = path.read_text(encoding="utf-8") if path.exists() else None
        parsed_cache[cache_key] = text
        return text
