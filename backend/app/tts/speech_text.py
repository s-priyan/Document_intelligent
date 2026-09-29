"""Turns markdown answer text into plain prose fit for a speech engine."""

import re

_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_TABLE_ROW = re.compile(r"^\s*\|.*$", re.MULTILINE)
_HORIZONTAL_RULE = re.compile(r"^\s*([-*_])\s*(?:\1\s*){2,}$", re.MULTILINE)
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_BLOCKQUOTE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+", re.MULTILINE)
_INLINE_CODE = re.compile(r"`([^`]*)`")
_EMPHASIS = re.compile(r"\*{1,3}|_{1,3}|~~")
_WHITESPACE = re.compile(r"\s+")


def to_spoken_text(markdown: str) -> str:
    """Strip markdown syntax so only words reach the speech engine.

    Formatting characters such as ``**`` would otherwise be read out loud, and
    code blocks, tables and link targets make for unlistenable speech, so they
    are dropped rather than narrated.

    :param markdown: A fragment of the markdown answer.
    :return: Plain text with collapsed whitespace, empty if nothing is speakable.
    """
    text = _FENCED_CODE.sub(" ", markdown)
    text = _IMAGE.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _TABLE_ROW.sub(" ", text)
    text = _HORIZONTAL_RULE.sub(" ", text)
    text = _HEADING.sub("", text)
    text = _BLOCKQUOTE.sub("", text)
    text = _LIST_MARKER.sub("", text)
    text = _INLINE_CODE.sub(r"\1", text)
    text = _EMPHASIS.sub("", text)
    return _WHITESPACE.sub(" ", text).strip()


def is_speakable(text: str) -> bool:
    """Report whether ``text`` is worth sending to the speech engine.

    Fragments left holding only punctuation after stripping (a stray ``.`` from
    a list marker, say) cost an API call and produce nothing useful.

    :param text: Candidate text to speak.
    :return: ``True`` when the text contains at least one letter or digit.
    """
    return any(character.isalnum() for character in text)
