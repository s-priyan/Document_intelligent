"""Adds spoken audio to a streamed answer without slowing the text down."""

import asyncio
import base64
import logging
from collections.abc import AsyncIterator

from app.schemas.query import AudioEvent, DeltaEvent, DoneEvent, QueryStreamEvent
from app.tts.speech_chunker import SpeechChunker
from app.tts.synthesizer import SpeechSynthesizer

logger = logging.getLogger(__name__)

BACKGROUND_TASK_COUNT = 2


class SpokenAnswerStream:
    """Interleave an ``audio`` event per spoken chunk into an answer stream.

    Synthesis happens in a background task feeding a queue, so a text delta is
    never held back by a speech call. Audio consequently trails the text it
    belongs to by roughly one chunk.
    """

    def __init__(self, synthesizer: SpeechSynthesizer) -> None:
        """Store the engine used to voice each sentence.

        :param synthesizer: Blocking speech engine, called off the event loop.
        """
        self._synthesizer = synthesizer

    async def stream(
        self, events: AsyncIterator[QueryStreamEvent]
    ) -> AsyncIterator[QueryStreamEvent]:
        """Republish ``events`` with an ``audio`` event per spoken sentence.

        :param events: The answer stream to voice; forwarded unchanged.
        :return: Async iterator over the original events plus audio events.
        """
        outbox: asyncio.Queue[QueryStreamEvent | None] = asyncio.Queue()
        chunks: asyncio.Queue[str | None] = asyncio.Queue()

        relay = asyncio.create_task(self._relay(events, outbox, chunks))
        speaker = asyncio.create_task(self._speak(chunks, outbox))
        finished = 0

        try:
            while finished < BACKGROUND_TASK_COUNT:
                event = await outbox.get()
                if event is None:
                    finished += 1
                    continue
                # Each background task posts one sentinel as it retires.

                yield event

            await relay
            await speaker
            # Surface failures the background tasks did not handle themselves.
        finally:
            for task in (relay, speaker):
                if not task.done():
                    task.cancel()

    @staticmethod
    async def _relay(
        events: AsyncIterator[QueryStreamEvent],
        outbox: "asyncio.Queue[QueryStreamEvent | None]",
        chunks: "asyncio.Queue[str | None]",
    ) -> None:
        """Forward every source event at once, queueing chunks to be spoken.

        The chunk queue is unbounded on purpose: bounding it would make a slow
        speech engine stall the text stream, which is what this class exists to
        prevent.

        :param events: The source answer stream.
        :param outbox: Queue of events to publish, terminated by ``None``.
        :param chunks: Queue of chunks to synthesize, terminated by ``None``.
        :return: None.
        """
        chunker = SpeechChunker()
        try:
            async for event in events:
                await outbox.put(event)
                if isinstance(event, DeltaEvent):
                    for chunk in chunker.push(event.text):
                        chunks.put_nowait(chunk)
                elif isinstance(event, DoneEvent):
                    for chunk in chunker.flush():
                        chunks.put_nowait(chunk)
                # A failed turn ends with an error event, leaving the tail unspoken.
        finally:
            chunks.put_nowait(None)
            outbox.put_nowait(None)

    async def _speak(
        self,
        chunks: "asyncio.Queue[str | None]",
        outbox: "asyncio.Queue[QueryStreamEvent | None]",
    ) -> None:
        """Voice queued chunks in order, dropping any that fail to synthesize.

        :param chunks: Queue of chunks to synthesize, terminated by ``None``.
        :param outbox: Queue of events to publish, terminated by ``None``.
        :return: None.
        """
        sequence = 0
        try:
            while True:
                chunk = await chunks.get()
                if chunk is None:
                    break
                # No further chunks will be queued.

                try:
                    audio = await asyncio.to_thread(self._synthesizer.synthesize, chunk)
                except Exception:  # speech backend failures must not break the answer
                    logger.exception("Speech synthesis failed | chunk=%r", chunk)
                    continue

                outbox.put_nowait(
                    AudioEvent(
                        sequence=sequence,
                        text=chunk,
                        audio_base64=base64.b64encode(audio).decode("ascii"),
                    )
                )
                sequence += 1
        finally:
            outbox.put_nowait(None)
