"""Discord 메시지 전송 — STT 결과를 Jarvis 봇에게 전달한다.

Bot 토큰 방식 (권장): DISCORD_BOT_TOKEN + DISCORD_CHANNEL_ID
  → 일반 봇 메시지로 전송되어 나노봇의 on_message 필터를 통과한다.

Webhook 방식 (폴백): DISCORD_WEBHOOK_URL
  → 나노봇이 webhook 메시지를 무시하도록 설정된 경우 반응 없음.
"""

import logging
import os

logger = logging.getLogger(__name__)


def send_to_jarvis(text: str) -> None:
    """STT 텍스트를 Discord로 전송한다 (Jarvis 멘션 포함)."""
    jarvis_id = os.getenv("DISCORD_JARVIS_BOT_ID", "")
    content = f"{text} <@{jarvis_id}>" if jarvis_id else text

    bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
    channel_id = os.getenv("DISCORD_CHANNEL_ID", "")

    if bot_token and channel_id:
        _send_via_bot(content, bot_token, channel_id)
    elif os.getenv("DISCORD_WEBHOOK_URL"):
        _send_via_webhook(content, os.getenv("DISCORD_WEBHOOK_URL"))
    else:
        logger.info(f"[MOCK Discord] Jarvis에게 전달: {content!r}")


def _send_via_bot(content: str, token: str, channel_id: str) -> None:
    """Bot 토큰으로 직접 채널에 메시지를 전송한다."""
    import requests

    try:
        resp = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
            },
            json={"content": content},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Discord Bot 전송 완료: {content!r}")
    except Exception as e:
        logger.error(f"Discord Bot 전송 실패: {e}")


def _send_via_webhook(content: str, webhook_url: str) -> None:
    """Webhook으로 메시지를 전송한다 (폴백)."""
    import requests

    try:
        resp = requests.post(
            webhook_url,
            json={"content": content},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Discord Webhook 전송 완료: {content!r}")
    except Exception as e:
        logger.error(f"Discord Webhook 전송 실패: {e}")
