"""Assembles streamed answer tokens into chunks worth synthesizing."""

from app.tts.speech_text import is_speakable, to_spoken_text

SENTENCE_BOUNDARIES = ".!?\n"
CODE_FENCE = "```"
TARGET_CHUNK_CHARS = 240
MAX_CHUNK_CHARS = 600


class SpeechChunker:
    """Group streamed answer text into batches for the speech engine.

    A speech request costs roughly the same in latency whatever its length, so
    synthesizing one short sentence at a time starves playback on list-heavy
    answers. Sentences are therefore batched towards ``TARGET_CHUNK_CHARS``.
    The opening chunk is an exception: it goes out as soon as a single sentence
    is ready, so the wait for the first words stays short.
    """

    def __init__(self) -> None:
        self._buffer = ""
        self._pending = ""
        self._in_code_block = False
        self._released_first = False

    def push(self, text: str) -> list[str]:
        """Add streamed text and return the chunks that are ready to speak.

        :param text: The next piece of answer text from the model.
        :return: Chunks in order; empty until enough text has accumulated.
        """
        self._buffer += text
        chunks: list[str] = []

        boundary = self._boundary_index(self._buffer)
        while boundary != -1:
            segment = self._buffer[: boundary + 1]
            self._buffer = self._buffer[boundary + 1 :]
            chunks.extend(self._absorb(segment))
            boundary = self._boundary_index(self._buffer)

        return chunks

    def flush(self) -> list[str]:
        """Release everything still held once the answer has ended.

        :return: The trailing chunks, or empty if nothing speakable remains.
        """
        remainder, self._buffer = self._buffer, ""
        chunks = self._absorb(remainder)
        if self._pending:
            chunks.append(self._release())
        return chunks

    def _absorb(self, segment: str) -> list[str]:
        """Add one raw segment to the pending chunk, releasing when it is full.

        :param segment: Raw markdown text up to and including a boundary.
        :return: Chunks completed by this segment, usually empty.
        """
        sentence = self._speakable(segment)
        if sentence is None:
            return []

        chunks: list[str] = []
        candidate = f"{self._pending} {sentence}" if self._pending else sentence
        if len(candidate) > MAX_CHUNK_CHARS and self._pending:
            chunks.append(self._release())
            candidate = sentence
        # Close the chunk rather than let a single request grow unbounded. A
        # lone sentence over the ceiling still goes out whole; splitting
        # mid-thought would be more audible than one slower request.

        self._pending = candidate
        if len(self._pending) >= self._threshold():
            chunks.append(self._release())

        return chunks

    def _speakable(self, segment: str) -> str | None:
        """Reduce a raw segment to speech text, or ``None`` if it is not spoken.

        :param segment: Raw markdown text to clean up.
        :return: Plain text to speak, or ``None`` to skip the segment.
        """
        if not segment:
            return None

        if segment.lstrip().startswith(CODE_FENCE):
            self._in_code_block = not self._in_code_block
            return None
        # A fence line only ever toggles the block; it is never spoken itself.

        if self._in_code_block:
            return None

        spoken = to_spoken_text(segment)
        return spoken if is_speakable(spoken) else None

    def _threshold(self) -> int:
        """Return the size at which the pending chunk should be released."""
        return TARGET_CHUNK_CHARS if self._released_first else 1

    def _release(self) -> str:
        """Hand over the pending chunk and start a new one."""
        chunk, self._pending = self._pending, ""
        self._released_first = True
        return chunk

    @staticmethod
    def _boundary_index(text: str) -> int:
        """Return the index of the first sentence-ending character, or -1.

        :param text: Buffered text to scan.
        :return: Index of the boundary character, or -1 if none is present.
        """
        for index, character in enumerate(text):
            if character in SENTENCE_BOUNDARIES:
                return index
        return -1
