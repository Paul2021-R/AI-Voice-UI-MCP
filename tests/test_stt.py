"""WhisperSTT 테스트 — 바이너리 없는 환경에서 Mock 동작 검증."""

import base64
import struct
from core.stt import WhisperSTT


def _make_dummy_wav() -> str:
    """최소한의 유효한 WAV base64 문자열을 생성한다."""
    sample_rate = 16000
    num_samples = 100
    data_size = num_samples * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1,
        sample_rate, sample_rate * 2, 2, 16,
        b"data", data_size,
    )
    samples = struct.pack(f"<{num_samples}h", *([0] * num_samples))
    return base64.b64encode(header + samples).decode()


def test_mock_transcribe_when_no_binary():
    stt = WhisperSTT()
    # 바이너리 없는 환경 (Linux CI) → Mock 텍스트 반환
    if not stt.is_available():
        result = stt.transcribe(_make_dummy_wav())
        assert isinstance(result, str)
        assert len(result) > 0


def test_parse_output_strips_timestamps():
    stt = WhisperSTT()
    raw = "[00:00:00.000 --> 00:00:01.500]  안녕하세요\n[00:00:01.500 --> 00:00:03.000]  반갑습니다"
    result = stt._parse_output(raw)
    assert "안녕하세요" in result
    assert "반갑습니다" in result
    assert "[" not in result
    assert "-->" not in result


def test_parse_output_no_timestamps():
    stt = WhisperSTT()
    result = stt._parse_output("  테스트 발화입니다  ")
    assert result == "테스트 발화입니다"


def test_parse_output_empty():
    stt = WhisperSTT()
    assert stt._parse_output("") == ""
