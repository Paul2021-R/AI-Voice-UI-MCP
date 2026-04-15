/**
 * 마이크 진폭 훅 — Python push 수신
 *
 * macOS WKWebView에서 navigator.mediaDevices가 차단되므로
 * Python(sounddevice)이 마이크를 캡처하고 진폭 데이터만 React로 푸시한다.
 */

import { useEffect, useState } from "react";
import { type AppState } from "../bridge";

export function useMicCapture(_state: AppState): { amplitude: number } {
  const [amplitude, setAmplitude] = useState(0);

  useEffect(() => {
    if (_state !== "LISTENING") {
      setAmplitude(0);
      return;
    }
    const handler = (e: Event) => {
      setAmplitude((e as CustomEvent<number>).detail);
    };
    window.addEventListener("mic-amplitude", handler);
    return () => window.removeEventListener("mic-amplitude", handler);
  }, [_state]);

  return { amplitude };
}
