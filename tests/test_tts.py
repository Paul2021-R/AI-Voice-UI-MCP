"""SupertoneTTS 테스트 — API 없는 환경에서 Mock 동작 검증."""

from core.tts import SupertoneTTS, _silent_wav


def test_mock_synthesize_returns_bytes_and_phonemes():
    tts = SupertoneTTS()
    if not tts.is_available():
        audio, phonemes = tts.synthesize("안녕하세요 반갑습니다")
        assert isinstance(audio, bytes)
        assert len(audio) > 0
        assert isinstance(phonemes, list)
        assert len(phonemes) == 2  # 단어 2개


def test_mock_phoneme_timing():
    tts = SupertoneTTS()
    if not tts.is_available():
        _, phonemes = tts.synthesize("hello world")
        assert phonemes[0]["text"] == "hello"
        assert phonemes[1]["text"] == "world"
        assert phonemes[0]["end_time"] == phonemes[1]["start_time"]


def test_silent_wav_header():
    wav = _silent_wav(1.0)
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"
    assert wav[12:16] == b"fmt "
    assert wav[36:40] == b"data"


def test_mock_synthesize_empty_text():
    tts = SupertoneTTS()
    if not tts.is_available():
        audio, phonemes = tts.synthesize("")
        assert isinstance(audio, bytes)
        assert phonemes == []
