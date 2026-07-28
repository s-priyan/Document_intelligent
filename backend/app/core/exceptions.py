"""Domain-level exceptions mapped to HTTP responses at the API boundary (FR-20)."""


class AppError(Exception):
    """Base class for expected application errors carrying an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Raised when an uploaded file fails type or size validation (FR-2)."""

    status_code = 422


class IndexNotFoundError(AppError):
    """Raised when a referenced knowledge index does not exist."""

    status_code = 404


class IndexAlreadyExistsError(AppError):
    """Raised when creating a knowledge index whose id already exists."""

    status_code = 409


class ParsingError(AppError):
    """Raised when Docling fails to extract content from a document (FR-3)."""

    status_code = 500


class IndexingError(AppError):
    """Raised when chunking, embedding or vector storage fails (FR-4/FR-5)."""

    status_code = 500


class QueryError(AppError):
    """Raised when retrieval or LLM answer generation fails (FR-9/FR-10)."""

    status_code = 502
