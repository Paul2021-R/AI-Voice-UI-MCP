"""Discord Webhook 테스트 — Mock 모드 동작 검증."""

from unittest.mock import patch, MagicMock
import os
from core.discord import send_to_jarvis


def test_mock_mode_when_no_webhook_url(caplog):
    os.environ.pop("DISCORD_WEBHOOK_URL", None)
    os.environ.pop("DISCORD_JARVIS_BOT_ID", None)
    import logging
    with caplog.at_level(logging.INFO, logger="core.discord"):
        send_to_jarvis("테스트 메시지")
    assert "MOCK Discord" in caplog.text


def test_sends_jarvis_mention():
    os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test"
    os.environ["DISCORD_JARVIS_BOT_ID"] = "123456789"

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        send_to_jarvis("안녕하세요")
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        assert "<@123456789>" in payload["content"]
        assert "안녕하세요" in payload["content"]

    os.environ.pop("DISCORD_WEBHOOK_URL", None)
    os.environ.pop("DISCORD_JARVIS_BOT_ID", None)
