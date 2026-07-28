"""Upload validation: file type and size checks (FR-2)."""

from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import ValidationError


class UploadValidator:
    """Validate uploaded files against allowed extensions and a size limit."""

    def __init__(self, settings: Settings) -> None:
        self._allowed_extensions = {ext.lower() for ext in settings.allowed_extensions}
        self._max_size_bytes = settings.max_file_size_bytes
        self._max_size_mb = settings.max_file_size_mb

    def validate(self, filename: str, size_bytes: int) -> None:
        """Validate a single file's extension and size.

        :raises ValidationError: if the type is unsupported, or the file is
            empty or larger than the configured limit.
        """
        extension = Path(filename).suffix.lower()
        if extension not in self._allowed_extensions:
            allowed = ", ".join(sorted(self._allowed_extensions))
            raise ValidationError(
                f"Unsupported file type '{extension or filename}'. Allowed types: {allowed}."
            )
        if size_bytes == 0:
            raise ValidationError(f"File '{filename}' is empty.")
        if size_bytes > self._max_size_bytes:
            raise ValidationError(
                f"File '{filename}' exceeds the maximum size of {self._max_size_mb} MB."
            )
