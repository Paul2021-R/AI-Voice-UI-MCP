"""Jarvis MCP 서버 — speak / cancel / get_state 도구를 노출한다."""

from mcp.server.fastmcp import FastMCP
from core.state import AppState, StateController

mcp = FastMCP("jarvis-voice-ui")
_state = StateController()
_app = None  # main.py에서 App 인스턴스를 주입한다


@mcp.tool()
def speak(text: str) -> str:
    """텍스트를 TTS로 변환하고 SPEAKING 상태로 진입한다. 윈도우가 없으면 자동으로 연다."""
    if _app:
        _app.on_speak_start()
        # TTS는 별도 스레드에서 실행
        # 재생 완료 시 React → notify_speak_done() → app.on_speak_done() 이 호출됨
        import threading
        threading.Thread(target=_run_tts, args=(text,), daemon=True).start()
    elif not _state.transition(AppState.SPEAKING):
        _state.force(AppState.SPEAKING)
    return f"speaking: {text}"


def _run_tts(text: str) -> None:
    """Supertone TTS 실행 후 오디오와 음소 데이터를 React로 푸시한다."""
    import base64
    import logging
    from core.tts import SupertoneTTS

    logger = logging.getLogger(__name__)
    try:
        tts = SupertoneTTS()
        audio_bytes, phonemes = tts.synthesize(text)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        if _app:
            _app.bridge.push_audio_and_phonemes(audio_b64, phonemes)
    except Exception as e:
        logger.error(f"TTS 오류: {e}")
        if _app:
            _app.on_cancel()


@mcp.tool()
def cancel() -> str:
    """재생을 중단하고 IDLE 상태로 전환한다."""
    if _app:
        _app.on_cancel()
    else:
        _state.force(AppState.IDLE)
    return "cancelled"


@mcp.tool()
def get_state() -> str:
    """현재 앱 상태를 반환한다."""
    src = _app.state if _app else _state
    return src.current.value


if __name__ == "__main__":
    mcp.run()
