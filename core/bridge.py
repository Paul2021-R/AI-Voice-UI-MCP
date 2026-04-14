"""pywebview에 노출할 Python API 클래스.

window.pywebview.api.method() 형태로 JS에서 호출된다.
Python → JS 푸시는 push_state() 를 통해 window.evaluate_js()로 전달한다.
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class PyWebViewAPI:
    """JS에서 호출 가능한 Python 메서드 모음."""

    def __init__(self) -> None:
        self._window = None
        self._get_state_cb: Callable[[], str] = lambda: "IDLE"
        self._on_stt_complete: Callable[[str], None] | None = None
        self._on_speak_done: Callable[[], None] | None = None

    def bind_window(self, window) -> None:
        """pywebview window 인스턴스를 주입한다 (macOS 전용)."""
        self._window = window

    def set_stt_callback(self, cb: Callable[[str], None]) -> None:
        """STT 완료 시 호출할 콜백을 등록한다 (App에서 주입)."""
        self._on_stt_complete = cb

    def set_speak_done_callback(self, cb: Callable[[], None]) -> None:
        """React TTS 재생 완료 시 호출할 콜백을 등록한다 (App에서 주입)."""
        self._on_speak_done: Callable[[], None] | None = cb

    # ------------------------------------------------------------------ #
    # JS → Python
    # ------------------------------------------------------------------ #

    def get_state(self) -> str:
        """현재 앱 상태를 반환한다."""
        return self._get_state_cb()

    def send_audio_chunk(self, b64_data: str) -> None:
        """마이크 캡처 오디오 청크(base64)를 수신한다 (스트리밍용 예비)."""
        logger.debug(f"audio chunk: {len(b64_data)} chars")

    def end_audio(self, wav_b64: str) -> None:
        """녹음 완료 후 16kHz WAV(base64)를 수신하고 STT를 실행한다."""
        logger.info(f"end_audio: wav_b64 length={len(wav_b64)}")
        if self._on_stt_complete:
            # STT는 블로킹 subprocess이므로 별도 스레드에서 실행
            import threading
            threading.Thread(
                target=self._run_stt,
                args=(wav_b64,),
                daemon=True,
            ).start()

    def _run_stt(self, wav_b64: str) -> None:
        from core.stt import WhisperSTT
        stt = WhisperSTT()
        text = stt.transcribe(wav_b64)
        logger.info(f"[STT] 변환 결과: {text!r}")
        if self._on_stt_complete:
            self._on_stt_complete(text)

    # ------------------------------------------------------------------ #
    # Python → JS
    # ------------------------------------------------------------------ #

    def notify_speak_done(self) -> None:
        """React TTS 재생 완료 신호를 수신한다 (JS → Python)."""
        logger.info("notify_speak_done 수신")
        if self._on_speak_done:
            self._on_speak_done()

    # ------------------------------------------------------------------ #
    # Python → JS
    # ------------------------------------------------------------------ #

    def push_state(self, state: str) -> None:
        """앱 상태를 React UI로 푸시한다."""
        if self._window:
            self._window.evaluate_js(
                f"window.__bridge && window.__bridge.onStateChange('{state}')"
            )
        else:
            logger.info(f"[MOCK] push_state → {state}")

    def push_audio_and_phonemes(self, audio_b64: str, phonemes: list) -> None:
        """TTS 오디오(base64)와 음소 타이밍 데이터를 React로 푸시한다."""
        import json
        phonemes_json = json.dumps(phonemes, ensure_ascii=False)
        if self._window:
            # evaluate_js 인수 크기 제한 고려 — 큰 오디오는 청크 전송으로 개선 가능
            self._window.evaluate_js(
                f"window.__bridge && window.__bridge.onAudioReady("
                f"'{audio_b64}', {phonemes_json})"
            )
        else:
            logger.info(
                f"[MOCK] push_audio_and_phonemes: "
                f"{len(audio_b64)} chars audio, {len(phonemes)} phonemes"
            )
