"""STT 흐름 통합 테스트."""

from core.app import App
from core.state import AppState


def _make_app() -> App:
    import os
    os.environ["WAITING_TIMEOUT_SEC"] = "10"
    return App()


def test_second_hotkey_triggers_processing():
    app = _make_app()
    app.start()
    app.hotkey.trigger()                      # IDLE → LISTENING
    assert app.state.current == AppState.LISTENING
    app.hotkey.trigger()                      # LISTENING → PROCESSING
    assert app.state.current == AppState.PROCESSING


def test_stt_callback_receives_text():
    received = []
    app = _make_app()
    app.bridge.set_stt_callback(lambda text: received.append(text))
    app.start()

    # end_audio 직접 호출 (브라우저 대신)
    import base64, struct
    num_samples = 100
    data_size = num_samples * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1,
        16000, 32000, 2, 16,
        b"data", data_size,
    )
    samples = struct.pack(f"<{num_samples}h", *([0] * num_samples))
    wav_b64 = base64.b64encode(header + samples).decode()

    import time
    app.bridge.end_audio(wav_b64)
    time.sleep(0.5)  # STT 스레드 대기

    assert len(received) == 1
    assert isinstance(received[0], str)
