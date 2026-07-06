"""Free TTS via Microsoft Edge — no API key, no Groq terms."""

from __future__ import annotations

import io
from dataclasses import dataclass

import av
import edge_tts
from livekit.agents import tts
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions

SAMPLE_RATE = 48000
NUM_CHANNELS = 1
DEFAULT_VOICE = "en-US-AriaNeural"


@dataclass
class _Opts:
    voice: str


class EdgeTTS(tts.TTS):
    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _Opts(voice=voice)

    @property
    def model(self) -> str:
        return self._opts.voice

    @property
    def provider(self) -> str:
        return "EdgeTTS"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return _Stream(tts=self, input_text=text, conn_options=conn_options)


class _Stream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        mp3 = bytearray()
        comm = edge_tts.Communicate(self._input_text, self._tts._opts.voice)
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                mp3.extend(chunk["data"])

        output_emitter.initialize(
            request_id="edge-tts",
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
            mime_type="audio/pcm",
        )

        container = av.open(io.BytesIO(bytes(mp3)), format="mp3")
        resampler = av.audio.resampler.AudioResampler(
            format="s16", layout="mono", rate=SAMPLE_RATE
        )
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                output_emitter.push(resampled.to_ndarray().tobytes())

        output_emitter.flush()
