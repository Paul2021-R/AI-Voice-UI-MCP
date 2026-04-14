"""Whisper.cpp 기반 로컬 STT 엔진.

macOS (실제): Whisper.cpp 바이너리 subprocess 실행
Linux/바이너리 없음: Mock 모드 — 고정 텍스트 반환
"""

import base64
import logging
import os
import re
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class WhisperSTT:
    """Whisper.cpp subprocess 래퍼."""

    def __init__(self) -> None:
        self._bin = os.getenv("WHISPER_BIN_PATH", "./bin/whisper")
        self._model = os.getenv("WHISPER_MODEL_PATH", "./models/ggml-medium.bin")

    def is_available(self) -> bool:
        return os.path.isfile(self._bin) and os.path.isfile(self._model)

    def transcribe(self, wav_b64: str) -> str:
        """base64 WAV를 받아 텍스트를 반환한다.

        Whisper.cpp 바이너리가 없으면 Mock 텍스트를 반환한다.
        """
        if not self.is_available():
            logger.info("[MOCK] STT — Whisper.cpp 없음, Mock 텍스트 반환")
            return "[Mock STT] 안녕하세요, 테스트 발화입니다."

        wav_bytes = base64.b64decode(wav_b64)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [
                    self._bin,
                    "-m", self._model,
                    "-f", tmp_path,
                    "-l", "ko",
                    "--no-timestamps",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.error(f"Whisper.cpp error: {result.stderr}")
                return ""

            text = self._parse_output(result.stdout)
            logger.info(f"STT result: {text!r}")
            return text
        finally:
            os.unlink(tmp_path)

    def _parse_output(self, output: str) -> str:
        """Whisper.cpp stdout에서 텍스트만 추출한다.

        타임스탬프 포맷: [00:00:00.000 --> 00:00:02.000]  텍스트
        --no-timestamps 시: 텍스트만 출력
        """
        lines = output.strip().splitlines()
        clean = []
        for line in lines:
            line = re.sub(
                r"\[\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\]\s*",
                "",
                line,
            ).strip()
            if line:
                clean.append(line)
        return " ".join(clean)
