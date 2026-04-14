"""엔트리포인트 — MCP 서버 + 앱 코어를 함께 실행한다."""

import logging
import threading

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from core.app import App
from mcp_server import mcp, _state as mcp_state

logger = logging.getLogger(__name__)


def main() -> None:
    app = App()
    app.start()

    # MCP 상태와 App 상태를 동기화
    # speak / cancel 호출 시 app 이벤트를 트리거하도록 연결
    # (TODO-004 브릿지 통합 후 pywebview.api 연동으로 대체)
    import mcp_server
    mcp_server._app = app

    logger.info("Starting MCP server (stdio)")
    mcp.run()


if __name__ == "__main__":
    main()
