"""앱 코어 — StateController / WindowManager / HotkeyListener / Bridge 조율."""

import logging
import os
import threading

from core.bridge import PyWebViewAPI
from core.hotkey import HotkeyListener
from core.state import AppState, StateController
from core.window import WindowManager

logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:
        timeout = float(os.getenv("WAITING_TIMEOUT_SEC", "10"))
        hotkey = os.getenv("HOTKEY", "<ctrl>+<space>")

        self.state = StateController()
        self.window = WindowManager(waiting_timeout=timeout)
        self.hotkey = HotkeyListener(hotkey, on_press=self._on_hotkey)
        self.bridge = PyWebViewAPI()
        self._mic = None  # core.mic.MicCapture 인스턴스

        # 상태 변경 시 React로 자동 푸시
        self.state.set_on_change(lambda s: self.bridge.push_state(s.value))
        self.bridge._get_state_cb = lambda: self.state.current.value

        # TTS 완료 콜백 연결
        self.bridge.set_speak_done_callback(self.on_speak_done)

        self.window.set_timeout_callback(self._on_waiting_timeout)

    # ------------------------------------------------------------------ #
    # 이벤트 핸들러
    # ------------------------------------------------------------------ #

    def _on_hotkey(self) -> None:
        current = self.state.current
        logger.info(f"Hotkey pressed (state={current.value})")

        if current in (AppState.IDLE, AppState.WAITING):
            self.state.transition(AppState.LISTENING)
            self.window.show()
            self._start_mic()
        elif current == AppState.LISTENING:
            # 두 번째 핫키 = 발화 완료 → PROCESSING + STT 시작
            self.state.transition(AppState.PROCESSING)
            self._stop_mic_and_transcribe()
        elif current == AppState.SPEAKING:
            # 재생 중 핫키 → LISTENING (ADR-001)
            self.state.force(AppState.LISTENING)
            self.window.show()
            self._start_mic()

    def _on_waiting_timeout(self) -> None:
        self.state.force(AppState.IDLE)
        logger.info("State → IDLE (waiting timeout)")

    def _start_mic(self) -> None:
        from core.mic import MicCapture
        self._mic = MicCapture(
            on_amplitude=lambda a: self.bridge.push_amplitude(a)
        )
        self._mic.start()

    def _stop_mic_and_transcribe(self) -> None:
        mic = self._mic
        self._mic = None
        if mic:
            threading.Thread(
                target=self._run_stt,
                args=(mic,),
                daemon=True,
            ).start()
        else:
            logger.warning("_stop_mic_and_transcribe: mic is None")

    def _run_stt(self, mic) -> None:
        wav_b64 = mic.stop()
        if not wav_b64:
            logger.warning("No audio captured — STT skipped")
            self.state.force(AppState.IDLE)
            return

        logger.info(f"Running STT on {len(wav_b64)} chars b64 WAV")
        from core.stt import WhisperSTT
        stt = WhisperSTT()
        text = stt.transcribe(wav_b64)
        logger.info(f"[STT 완료] {text!r}")

        if text:
            from core.discord import send_to_jarvis
            send_to_jarvis(text)
        else:
            logger.warning("STT returned empty — back to IDLE")
            self.state.force(AppState.IDLE)

    # ------------------------------------------------------------------ #
    # 외부 진입점 (MCP 도구에서 호출)
    # ------------------------------------------------------------------ #

    def on_speak_start(self) -> None:
        if not self.state.transition(AppState.SPEAKING):
            self.state.force(AppState.SPEAKING)
        self.window.show()

    def on_speak_done(self) -> None:
        if self.state.transition(AppState.WAITING):
            self.window.start_waiting_timer()

    def on_cancel(self) -> None:
        self.state.force(AppState.IDLE)
        self.window.hide()

    # ------------------------------------------------------------------ #
    # 시작
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        self.window.start(api=self.bridge)
        self.hotkey.start()
        logger.info("App started — waiting for hotkey or MCP call")
