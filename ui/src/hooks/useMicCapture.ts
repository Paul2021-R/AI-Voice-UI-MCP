/**
 * 마이크 캡처 훅 — AppState와 연동하여 자동 시작/종료한다.
 *
 * LISTENING 진입  → mic.start()
 * LISTENING 종료  → mic.stop() → end_audio(wav_b64) 호출
 */

import { useEffect, useRef, useState } from "react";
import { MicCapture } from "../audio/MicCapture";
import { getApi } from "../bridge";
import { type AppState } from "../bridge";

export function useMicCapture(state: AppState): { amplitude: number } {
  const micRef = useRef<MicCapture | null>(null);
  const [amplitude, setAmplitude] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (state === "LISTENING") {
      const mic = new MicCapture();
      micRef.current = mic;

      mic.start().catch((err) => {
        console.error("[MicCapture] start failed:", err);
      });

      // amplitude 폴링
      const tick = () => {
        setAmplitude(micRef.current?.amplitude ?? 0);
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } else {
      // LISTENING이 아니면 녹음 중지 및 전송
      cancelAnimationFrame(rafRef.current);
      setAmplitude(0);

      const mic = micRef.current;
      micRef.current = null;

      if (mic?.isRunning) {
        mic.stop().then((wav_b64) => {
          if (!wav_b64) return;
          console.log("[MicCapture] recording done, sending to Python");
          getApi()
            ?.end_audio(wav_b64)
            .catch((err) => console.error("[MicCapture] end_audio failed:", err));
        });
      }
    }

    return () => cancelAnimationFrame(rafRef.current);
  }, [state]);

  return { amplitude };
}
