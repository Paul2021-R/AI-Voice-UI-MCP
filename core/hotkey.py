"""pynput 기반 글로벌 핫키 감지.

macOS: pynput.keyboard.GlobalHotKeys 실제 사용
Linux/기타: Mock 모드 — trigger()로 수동 시뮬레이션
"""

import logging
import sys
import threading
from typing import Callable

logger = logging.getLogger(__name__)

IS_MACOS = sys.platform == "darwin"


class HotkeyListener:
    """글로벌 핫키를 감지하여 콜백을 호출한다."""

    def __init__(self, hotkey: str, on_press: Callable[[], None]) -> None:
        self._hotkey = hotkey
        self._on_press = on_press
        self._listener = None

    def start(self) -> None:
        """핫키 감지를 백그라운드 스레드에서 시작한다."""
        if IS_MACOS:
            from pynput import keyboard

            self._listener = keyboard.GlobalHotKeys({self._hotkey: self._on_press})
            t = threading.Thread(target=self._listener.start, daemon=True)
            t.start()
            logger.info(f"HotkeyListener started: '{self._hotkey}'")
        else:
            logger.info(f"[MOCK] HotkeyListener ready: '{self._hotkey}'")
            logger.info("[MOCK] trigger() 로 핫키를 시뮬레이션할 수 있습니다")

    def trigger(self) -> None:
        """테스트/Linux 개발 환경에서 핫키를 수동으로 시뮬레이션한다."""
        logger.info(f"[MOCK] Hotkey triggered: '{self._hotkey}'")
        self._on_press()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
