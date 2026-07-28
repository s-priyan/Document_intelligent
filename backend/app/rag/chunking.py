"""Recursive text chunking for embedding and retrieval (FR-4)."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings


class DocumentChunker:
    """Split extracted document text into overlapping, retrieval-sized chunks."""

    def __init__(self, settings: Settings) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            add_start_index=True,
        )

    def chunk(self, text: str, metadata: dict) -> list[Document]:
        """Split ``text`` into LangChain documents, each carrying ``metadata``.

        ``add_start_index`` records each chunk's character offset in the source,
        which becomes part of the stored citation metadata (FR-5).
        """
        return self._splitter.create_documents([text], metadatas=[dict(metadata)])
