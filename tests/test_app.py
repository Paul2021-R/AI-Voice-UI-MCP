import time

from core.app import App
from core.state import AppState


def _make_app(timeout: float = 0.1) -> App:
    import os
    os.environ["WAITING_TIMEOUT_SEC"] = str(timeout)
    return App()


def test_hotkey_idle_to_listening():
    app = _make_app()
    app.start()
    app.hotkey.trigger()
    assert app.state.current == AppState.LISTENING


def test_hotkey_waiting_to_listening():
    app = _make_app()
    app.start()
    app.hotkey.trigger()                      # IDLE → LISTENING
    app.state.force(AppState.WAITING)         # WAITING으로 강제 이동
    app.hotkey.trigger()                      # WAITING → LISTENING
    assert app.state.current == AppState.LISTENING


def test_speak_cancel_flow():
    app = _make_app()
    app.start()
    app.on_speak_start()
    assert app.state.current == AppState.SPEAKING
    app.on_cancel()
    assert app.state.current == AppState.IDLE


def test_waiting_timeout_resets_to_idle():
    app = _make_app(timeout=0.1)
    app.start()
    app.on_speak_start()
    app.on_speak_done()
    assert app.state.current == AppState.WAITING
    time.sleep(0.3)
    assert app.state.current == AppState.IDLE


def test_hotkey_during_speaking_cancels():
    app = _make_app()
    app.start()
    app.on_speak_start()
    assert app.state.current == AppState.SPEAKING
    app.hotkey.trigger()                      # 재생 중 핫키 → LISTENING
    assert app.state.current == AppState.LISTENING
