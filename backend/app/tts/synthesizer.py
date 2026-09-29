"""Speech synthesis backed by the Gemini text-to-speech models."""

import io
import wave

from google import genai
from google.genai import types

from app.core.config import Settings

SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2
CHANNELS = 1

# Framing the transcript as a read-aloud instruction stops the TTS model from
# treating short inputs (e.g. "Hello!") as a chat prompt and replying with text,
# which the API rejects with a 400 INVALID_ARGUMENT. The prefix is not spoken.
READ_ALOUD_INSTRUCTION = "Read the following text aloud exactly as written: "


class SpeechSynthesizer:
    """Convert a sentence of answer text into playable audio."""

    def __init__(self, settings: Settings) -> None:
        """Create the Gemini client and capture the model and voice to use.

        :param settings: Runtime settings supplying the API key, model and voice.
        """
        self._model = settings.tts_model
        self._voice = settings.tts_voice
        self._client = genai.Client(api_key=settings.google_api_key)

    def synthesize(self, text: str) -> bytes:
        """Synthesize ``text`` into a self-describing WAV payload.

        This issues a blocking network call, so callers running on the event
        loop must dispatch it to a worker thread.

        :param text: The chunk of answer text to read aloud.
        :return: WAV-encoded audio bytes.
        :raises ValueError: If the model returned no audio.
        """
        response = self._client.models.generate_content(
            model=self._model,
            contents=f"{READ_ALOUD_INSTRUCTION}{text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self._voice
                        )
                    )
                ),
            ),
        )
        return self._to_wav(self._extract_pcm(response))

    @staticmethod
    def _extract_pcm(response: types.GenerateContentResponse) -> bytes:
        """Pull the raw PCM payload out of a synthesis response.

        :param response: The model response to read the audio part from.
        :return: Raw PCM bytes (24kHz, mono, 16-bit).
        :raises ValueError: If the response carries no inline audio data.
        """
        candidates = response.candidates or []
        parts = candidates[0].content.parts if candidates and candidates[0].content else []
        for part in parts or []:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data

        raise ValueError("No audio data received from the speech model.")

    @staticmethod
    def _to_wav(pcm: bytes) -> bytes:
        """Wrap raw PCM in a WAV container so browsers can decode it directly.

        :param pcm: Raw PCM bytes (24kHz, mono, 16-bit).
        :return: The same audio as a WAV file payload.
        """
        container = io.BytesIO()
        with wave.open(container, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(pcm)
        return container.getvalue()
