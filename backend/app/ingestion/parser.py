"""Document parsing with Docling (FR-3).

Text-native formats (``.txt``, ``.md``) are read directly; binary formats
(``.pdf``, ``.docx``) are converted to markdown via Docling so that structure
such as headings and tables is preserved.
"""

from functools import lru_cache
from pathlib import Path

from app.core.exceptions import ParsingError

_TEXT_EXTENSIONS = {".txt", ".md"}


@lru_cache
def _get_converter():
    """Lazily build a Docling ``DocumentConverter`` (heavy import, built once)."""
    from docling.document_converter import DocumentConverter

    return DocumentConverter()


class DocumentParser:
    """Extract clean markdown text from a document on disk."""

    def parse(self, file_path: Path) -> str:
        """Parse a document and return its content as markdown.

        :raises ParsingError: if extraction fails.
        """
        if file_path.suffix.lower() in _TEXT_EXTENSIONS:
            return self._read_text(file_path)
        return self._convert_with_docling(file_path)

    def _read_text(self, file_path: Path) -> str:
        """Read a text-native file directly from disk.

        :raises ParsingError: if the file cannot be read.
        """
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ParsingError(f"Could not read '{file_path.name}': {exc}") from exc

    def _convert_with_docling(self, file_path: Path) -> str:
        """Convert a binary document to markdown using Docling.

        :raises ParsingError: if Docling fails to convert the document.
        """
        try:
            result = _get_converter().convert(str(file_path))
            return result.document.export_to_markdown()
        except Exception as exc:  # Docling surfaces a range of backend errors.
            raise ParsingError(f"Failed to parse '{file_path.name}': {exc}") from exc
