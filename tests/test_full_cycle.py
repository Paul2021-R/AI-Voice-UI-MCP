"""전체 사이클 통합 테스트 — SPEAKING → WAITING → IDLE."""

import time
from core.app import App
from core.state import AppState


def _make_app(timeout: float = 0.1) -> App:
    import os
    os.environ["WAITING_TIMEOUT_SEC"] = str(timeout)
    return App()


def test_speak_done_transitions_to_waiting():
    app = _make_app(timeout=10)
    app.start()
    app.on_speak_start()
    assert app.state.current == AppState.SPEAKING
    app.on_speak_done()
    assert app.state.current == AppState.WAITING


def test_waiting_timeout_transitions_to_idle():
    app = _make_app(timeout=0.1)
    app.start()
    app.on_speak_start()
    app.on_speak_done()
    assert app.state.current == AppState.WAITING
    time.sleep(0.3)
    assert app.state.current == AppState.IDLE


def test_full_cycle_hotkey_to_idle():
    """핫키 → LISTENING → PROCESSING → SPEAKING → WAITING → IDLE 전체 사이클."""
    app = _make_app(timeout=0.1)
    app.start()

    app.hotkey.trigger()
    assert app.state.current == AppState.LISTENING

    app.hotkey.trigger()
    assert app.state.current == AppState.PROCESSING

    # STT 완료 → speak 호출 (Jarvis 응답 시뮬레이션)
    app.on_speak_start()
    assert app.state.current == AppState.SPEAKING

    app.on_speak_done()
    assert app.state.current == AppState.WAITING

    time.sleep(0.3)
    assert app.state.current == AppState.IDLE


def test_notify_speak_done_via_bridge():
    """React → notify_speak_done() → on_speak_done() 체인 검증."""
    app = _make_app(timeout=10)
    app.start()
    app.on_speak_start()
    assert app.state.current == AppState.SPEAKING

    # React에서 재생 완료 신호
    app.bridge.notify_speak_done()
    assert app.state.current == AppState.WAITING
