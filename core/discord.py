"""Discord Webhook 전송 — STT 결과를 Jarvis 봇에게 전달한다."""

import logging
import os

logger = logging.getLogger(__name__)


def send_to_jarvis(text: str) -> None:
    """STT 텍스트를 Discord Webhook으로 전송한다 (Jarvis 멘션 포함).

    환경변수가 없는 개발 환경에서는 로그만 출력한다.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    jarvis_id = os.getenv("DISCORD_JARVIS_BOT_ID", "")

    if not webhook_url:
        logger.info(f"[MOCK Discord] Jarvis에게 전달: {text!r}")
        return

    content = f"<@{jarvis_id}> {text}" if jarvis_id else text

    import requests  # API 키 있는 환경에서만 임포트

    try:
        resp = requests.post(
            webhook_url,
            json={"content": content},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Discord 전송 완료: {content!r}")
    except Exception as e:
        logger.error(f"Discord 전송 실패: {e}")
