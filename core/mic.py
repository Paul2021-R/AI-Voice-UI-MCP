"""Python-side 마이크 캡처 — sounddevice 기반.

WKWebView(macOS)에서 navigator.mediaDevices가 차단되므로
Python에서 직접 오디오를 캡처한다.
"""

import base64
import io
import logging
import threading
import wave
from typing import Callable

logger = logging.getLogger(__name__)


class MicCapture:
    """sounddevice를 이용한 마이크 캡처."""

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, on_amplitude: Callable[[float], None] | None = None) -> None:
        self._on_amplitude = on_amplitude
        self._chunks: list = []
        self._stream = None
        self._running = False
        self._amplitude = 0.0
        self._amp_timer: threading.Timer | None = None

    def start(self) -> None:
        import numpy as np
        import sounddevice as sd

        self._chunks = []
        self._running = True

        def callback(indata, frames, time, status) -> None:
            if self._running:
                self._chunks.append(indata.copy())
                rms = float(np.sqrt(np.mean(indata ** 2)))
                self._amplitude = min(1.0, rms * 6)

        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()
        self._schedule_amp_push()
        logger.info("MicCapture started")

    def _schedule_amp_push(self) -> None:
        if not self._running:
            return
        if self._on_amplitude:
            try:
                self._on_amplitude(self._amplitude)
            except Exception:
                pass
        self._amp_timer = threading.Timer(0.1, self._schedule_amp_push)
        self._amp_timer.daemon = True
        self._amp_timer.start()

    def stop(self) -> str:
        """녹음 중지 후 base64 WAV 문자열 반환."""
        import numpy as np

        self._running = False
        if self._amp_timer:
            self._amp_timer.cancel()
            self._amp_timer = None

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._chunks:
            logger.warning("MicCapture: 녹음된 오디오 없음")
            return ""

        audio = np.concatenate(self._chunks, axis=0).flatten()
        wav_bytes = self._to_wav(audio)
        logger.info(f"MicCapture stopped: {len(wav_bytes)} bytes WAV")
        return base64.b64encode(wav_bytes).decode()

    def _to_wav(self, samples) -> bytes:
        import numpy as np

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
            wf.writeframes(int16.tobytes())
        return buf.getvalue()
