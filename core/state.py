from enum import Enum
from threading import Lock
from typing import Callable


class AppState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    WAITING = "WAITING"


# 유효한 상태 전이 규칙
_TRANSITIONS: dict[AppState, set[AppState]] = {
    AppState.IDLE:       {AppState.LISTENING, AppState.SPEAKING},
    AppState.LISTENING:  {AppState.PROCESSING, AppState.IDLE},
    AppState.PROCESSING: {AppState.SPEAKING, AppState.IDLE},
    AppState.SPEAKING:   {AppState.WAITING, AppState.IDLE},
    AppState.WAITING:    {AppState.LISTENING, AppState.IDLE},
}


class StateController:
    """앱 상태의 Single Source of Truth."""

    def __init__(self) -> None:
        self._state = AppState.IDLE
        self._lock = Lock()
        self._on_change: Callable[[AppState], None] | None = None

    def set_on_change(self, callback: Callable[[AppState], None]) -> None:
        """상태 변경 시 호출할 콜백을 등록한다 (브릿지 푸시용)."""
        self._on_change = callback

    @property
    def current(self) -> AppState:
        with self._lock:
            return self._state

    def transition(self, target: AppState) -> bool:
        """상태 전이를 시도한다. 유효하면 True, 아니면 False를 반환한다."""
        with self._lock:
            if target in _TRANSITIONS.get(self._state, set()):
                self._state = target
                changed = True
            else:
                changed = False
        if changed and self._on_change:
            self._on_change(target)
        return changed

    def force(self, target: AppState) -> None:
        """유효성 검사 없이 강제 전이한다 (cancel 등 긴급 상황용)."""
        with self._lock:
            self._state = target
        if self._on_change:
            self._on_change(target)
