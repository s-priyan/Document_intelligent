"""Tests for batching streamed markdown tokens into speakable chunks."""

from app.tts.speech_chunker import MAX_CHUNK_CHARS, TARGET_CHUNK_CHARS, SpeechChunker
from app.tts.speech_text import to_spoken_text


def push_all(tokens: list[str]) -> list[str]:
    """Feed every token through a fresh chunker and flush the tail."""
    chunker = SpeechChunker()
    chunks = []
    for token in tokens:
        chunks.extend(chunker.push(token))
    chunks.extend(chunker.flush())
    return chunks


def test_the_opening_chunk_is_released_as_soon_as_a_sentence_ends() -> None:
    chunker = SpeechChunker()

    assert chunker.push("Hello") == []
    # Nothing is spoken until a sentence actually ends.
    assert chunker.push(" there. Next") == ["Hello there."]


def test_later_sentences_are_batched_towards_the_target_size() -> None:
    sentence = "A model tends to write sentences of roughly this sort of length."

    chunks = push_all([f"{sentence} "] * 6)

    assert chunks[0] == sentence
    # Only the opening chunk is allowed to be short; the rest are batched up to
    # the target, and the tail flushed at the end may be short again.
    assert all(len(chunk) >= TARGET_CHUNK_CHARS for chunk in chunks[1:-1])
    assert all(len(chunk) <= MAX_CHUNK_CHARS for chunk in chunks)
    assert " ".join(chunks) == " ".join([sentence] * 6)


def test_a_sentence_over_the_ceiling_is_passed_through_whole() -> None:
    long_sentence = f"{'word ' * 200}".strip()

    chunks = push_all(["Opening line. ", f"{long_sentence}."])

    assert chunks == ["Opening line.", f"{long_sentence}."]


def test_markdown_formatting_is_not_spoken() -> None:
    assert push_all(["## Summary\n", "The **net** total is `42`.\n"]) == [
        "Summary",
        "The net total is 42.",
    ]


def test_fenced_code_blocks_are_skipped() -> None:
    tokens = ["Run this.\n", "```python\n", "print('hi')\n", "```\n", "Done.\n"]

    assert push_all(tokens) == ["Run this.", "Done."]


def test_punctuation_only_fragments_are_not_spoken() -> None:
    assert push_all(["...\n"]) == []


def test_link_targets_are_dropped_but_labels_kept() -> None:
    assert to_spoken_text("See [the report](https://example.com/a).") == "See the report."


def test_table_rows_are_dropped() -> None:
    assert to_spoken_text("| Quarter | Revenue |") == ""
