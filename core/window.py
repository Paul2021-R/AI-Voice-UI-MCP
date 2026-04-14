"""pywebview 기반 Instant-on 윈도우 라이프사이클 관리.

macOS: pywebview 실제 사용
Linux/기타: Mock 모드 (로그 출력)
"""

import logging
import sys
import threading
from typing import Callable

logger = logging.getLogger(__name__)

IS_MACOS = sys.platform == "darwin"


class WindowManager:
    """윈도우를 최초 1회 생성 후 Hide/Show로 제어하는 Instant-on 매니저."""

    def __init__(self, waiting_timeout: float = 10.0) -> None:
        self._window = None
        self._api = None  # PyWebViewAPI 인스턴스 (js_api로 전달)
        self._ready = threading.Event()
        self._waiting_timer: threading.Timer | None = None
        self._timeout = waiting_timeout
        self._on_timeout_cb: Callable[[], None] | None = None

    def set_timeout_callback(self, callback: Callable[[], None]) -> None:
        """WAITING 타임아웃 시 호출할 콜백을 등록한다."""
        self._on_timeout_cb = callback

    def start(self, api=None) -> None:
        """백그라운드 스레드에서 webview를 초기화한다 (숨김 상태로 생성).

        Args:
            api: PyWebViewAPI 인스턴스. js_api로 pywebview에 전달되며
                 window.pywebview.api 로 JS에서 접근 가능해진다.
        """
        self._api = api
        if IS_MACOS:
            t = threading.Thread(target=self._run_webview, daemon=True)
            t.start()
            self._ready.wait()
        else:
            logger.info("[MOCK] WindowManager started (hidden)")
            self._ready.set()

    def _run_webview(self) -> None:
        import webview  # macOS 전용

        self._window = webview.create_window(
            "AI Voice UI",
            "ui/dist/index.html",
            width=800,
            height=600,
            frameless=True,
            hidden=True,
            js_api=self._api,  # window.pywebview.api 로 JS에 노출
        )
        # bridge가 push_state(evaluate_js) 를 쓸 수 있도록 window 인스턴스 주입
        if self._api and hasattr(self._api, "bind_window"):
            self._api.bind_window(self._window)
        self._ready.set()
        webview.start()

    def show(self) -> None:
        """윈도우를 표시하고 WAITING 타이머를 취소한다."""
        self._cancel_waiting_timer()
        if IS_MACOS and self._window:
            self._window.show()
        else:
            logger.info("[MOCK] Window → SHOW")

    def hide(self) -> None:
        """윈도우를 숨긴다 (destroy 하지 않음)."""
        self._cancel_waiting_timer()
        if IS_MACOS and self._window:
            self._window.hide()
        else:
            logger.info("[MOCK] Window → HIDE")

    def start_waiting_timer(self) -> None:
        """WAITING 상태 진입 시 호출. 타임아웃 후 윈도우를 숨긴다."""
        self._cancel_waiting_timer()
        self._waiting_timer = threading.Timer(self._timeout, self._on_waiting_timeout)
        self._waiting_timer.daemon = True
        self._waiting_timer.start()
        logger.info(f"[WAITING] {self._timeout}s 후 윈도우 숨김")

    def _cancel_waiting_timer(self) -> None:
        if self._waiting_timer:
            self._waiting_timer.cancel()
            self._waiting_timer = None

    def _on_waiting_timeout(self) -> None:
        logger.info("[WAITING] 타임아웃 — 윈도우 숨김")
        self.hide()
        if self._on_timeout_cb:
            self._on_timeout_cb()
