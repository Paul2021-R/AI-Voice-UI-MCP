"""앱 코어 — StateController / WindowManager / HotkeyListener / Bridge 조율."""

import logging
import os

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

        # 상태 변경 시 React로 자동 푸시
        self.state.set_on_change(lambda s: self.bridge.push_state(s.value))
        self.bridge._get_state_cb = lambda: self.state.current.value

        # STT / TTS 완료 콜백 연결
        self.bridge.set_stt_callback(self._on_stt_complete)
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
        elif current == AppState.LISTENING:
            # 두 번째 핫키 = 발화 완료 → PROCESSING
            # React가 PROCESSING 감지 후 end_audio(wav_b64) 를 호출한다
            self.state.transition(AppState.PROCESSING)
        elif current == AppState.SPEAKING:
            # 재생 중 핫키 → LISTENING (ADR-001)
            self.state.force(AppState.LISTENING)
            self.window.show()

    def _on_waiting_timeout(self) -> None:
        self.state.force(AppState.IDLE)
        logger.info("State → IDLE (waiting timeout)")

    def _on_stt_complete(self, text: str) -> None:
        """STT 완료 — Discord Webhook으로 Jarvis에게 전달한다."""
        logger.info(f"[STT 완료] {text!r}")
        from core.discord import send_to_jarvis
        send_to_jarvis(text)

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
