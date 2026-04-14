"""Supertone Stream TTS 클라이언트.

API 키/Voice ID 없는 환경: Mock 무음 WAV + 단어 단위 phoneme 반환
"""

import base64
import logging
import os
import struct

logger = logging.getLogger(__name__)

# Supertone API 응답의 phoneme 형식
# {"text": str, "start_time": float, "end_time": float}
Phoneme = dict


class SupertoneTTS:
    BASE_URL = "https://api.supertone.ai"

    def __init__(self) -> None:
        self._api_key = os.getenv("SUPERTONE_API_KEY", "")
        self._voice_id = os.getenv("SUPERTONE_VOICE_ID", "")
        self._style = os.getenv("SUPERTONE_STYLE", "normal")
        self._language = os.getenv("SUPERTONE_LANGUAGE", "ko")
        self._model = os.getenv("SUPERTONE_MODEL", "sona_speech_2")

    def is_available(self) -> bool:
        return bool(self._api_key and self._voice_id)

    def synthesize(self, text: str) -> tuple[bytes, list[Phoneme]]:
        """텍스트를 음성으로 변환한다.

        Returns:
            (audio_bytes, phonemes) — phonemes는 단어 단위 타이밍 리스트
        """
        if not self.is_available():
            return self._mock_synthesize(text)

        import requests  # macOS / API 키 있는 환경에서만 임포트

        try:
            resp = requests.post(
                f"{self.BASE_URL}/v1/speech",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "voice_id": self._voice_id,
                    "style": self._style,
                    "language": self._language,
                    "model": self._model,
                    "include_phonemes": True,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            audio_bytes = base64.b64decode(data.get("audio", ""))
            phonemes: list[Phoneme] = data.get("phonemes", [])
            logger.info(f"TTS 완료: {len(audio_bytes)} bytes, {len(phonemes)} phonemes")
            return audio_bytes, phonemes

        except Exception as e:
            logger.error(f"Supertone API 오류: {e} — Mock으로 폴백")
            return self._mock_synthesize(text)

    def _mock_synthesize(self, text: str) -> tuple[bytes, list[Phoneme]]:
        logger.info(f"[MOCK TTS] {text!r}")
        duration = 2.0
        audio_bytes = _silent_wav(duration)
        words = text.split()
        word_dur = duration / max(len(words), 1)
        phonemes: list[Phoneme] = [
            {
                "text": w,
                "start_time": round(i * word_dur, 3),
                "end_time": round((i + 1) * word_dur, 3),
            }
            for i, w in enumerate(words)
        ]
        return audio_bytes, phonemes


def _silent_wav(seconds: float, sample_rate: int = 22050) -> bytes:
    """지정된 길이의 무음 WAV 바이트를 생성한다."""
    num_samples = int(sample_rate * seconds)
    data_size = num_samples * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1,
        sample_rate, sample_rate * 2, 2, 16,
        b"data", data_size,
    )
    return header + bytes(data_size)
