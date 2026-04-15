"""엔트리포인트 — MCP 서버 + 앱 코어를 함께 실행한다."""

import logging
import threading

from pathlib import Path
from dotenv import load_dotenv

# 실행 위치와 무관하게 project/ 또는 repo 루트의 .env를 로드한다
_here = Path(__file__).parent
load_dotenv(_here / ".env")           # project/.env
load_dotenv(_here.parent / ".env")    # repo 루트/.env

_log_file = Path.home() / "jarvis-voice-ui.log"
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_file_handler = logging.FileHandler(_log_file, encoding="utf-8")
_file_handler.setFormatter(_fmt)
logging.basicConfig(level=logging.INFO, format=_fmt._fmt)
logging.getLogger().addHandler(_file_handler)  # basicConfig 무시 여부와 무관하게 강제 추가

from core.app import App
from mcp_server import mcp, _state as mcp_state

logger = logging.getLogger(__name__)


def main() -> None:
    import sys

    app = App()

    import mcp_server
    mcp_server._app = app

    if sys.platform == "darwin":
        # macOS: pywebview는 메인 스레드 필요 → MCP를 백그라운드로 실행
        app.window.prepare(api=app.bridge)
        app.hotkey.start()

        mcp_thread = threading.Thread(target=_run_mcp, daemon=True)
        mcp_thread.start()

        logger.info("Starting pywebview main loop (main thread)")
        app.window.run_webview()
    else:
        app.start()
        logger.info("Starting MCP server (stdio)")
        mcp.run()


def _run_mcp() -> None:
    logger.info("Starting MCP server (stdio, background thread)")
    mcp.run()


if __name__ == "__main__":
    main()
