"""Tests for interleaving spoken audio into a streamed answer.

A fake speech engine stands in for Gemini, so no network call is made and the
audio payloads are readable strings.
"""

import asyncio
import base64

from app.schemas.query import CitationsEvent, DeltaEvent, DoneEvent, QueryStreamEvent
from app.services.speech_stream import SpokenAnswerStream


def run_stream(synthesizer, events: list[QueryStreamEvent]) -> list[QueryStreamEvent]:
    """Drive the spoken stream over a scripted source and collect its output."""

    async def source():
        for event in events:
            yield event

    async def drain() -> list[QueryStreamEvent]:
        spoken = SpokenAnswerStream(synthesizer).stream(source())
        return [event async for event in spoken]

    return asyncio.run(drain())


def test_text_events_are_forwarded_unchanged(synthesizer) -> None:
    events = [
        CitationsEvent(citations=[]),
        DeltaEvent(text="Hi there. "),
        DeltaEvent(text="Bye now."),
        DoneEvent(answer="Hi there. Bye now."),
    ]

    published = run_stream(synthesizer, events)

    assert [event for event in published if event.event != "audio"] == events


def test_each_sentence_is_spoken_once_in_order(synthesizer) -> None:
    events = [
        DeltaEvent(text="Hi there. "),
        DeltaEvent(text="Bye now."),
        DoneEvent(answer="Hi there. Bye now."),
    ]

    audio = [event for event in run_stream(synthesizer, events) if event.event == "audio"]

    assert [event.text for event in audio] == ["Hi there.", "Bye now."]
    assert [event.sequence for event in audio] == [0, 1]
    assert synthesizer.spoken == ["Hi there.", "Bye now."]
    assert base64.b64decode(audio[0].audio_base64) == b"wav:Hi there."
    assert audio[0].mime_type == "audio/wav"


def test_the_trailing_sentence_is_spoken_even_without_punctuation(synthesizer) -> None:
    events = [DeltaEvent(text="No full stop here"), DoneEvent(answer="No full stop here")]

    published = run_stream(synthesizer, events)

    assert [event.text for event in published if event.event == "audio"] == [
        "No full stop here"
    ]


def test_a_speech_failure_leaves_the_answer_intact(synthesizer) -> None:
    synthesizer.failure = RuntimeError("speech backend exploded")
    events = [DeltaEvent(text="Hi there."), DoneEvent(answer="Hi there.")]

    published = run_stream(synthesizer, events)

    # The sentence was attempted, dropped, and the text stream survived whole.
    assert synthesizer.spoken == ["Hi there."]
    assert published == events
