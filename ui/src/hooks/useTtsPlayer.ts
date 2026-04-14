/**
 * TTS 재생 훅 — Python push 수신 → 오디오 재생 + 음소 싱크 연동
 *
 * 이벤트 흐름:
 * tts-audio-ready CustomEvent 수신
 *   → TtsPlayer.play()
 *   → usePhonemeSync.start(phonemes, audioContext)
 *   → 재생 완료 → api.notify_speak_done() → Python on_speak_done()
 */

import { useEffect, useRef } from "react";
import { TtsPlayer } from "../audio/TtsPlayer";
import { type Phoneme, usePhonemeSync } from "./usePhonemeSync";
import { getApi } from "../bridge";

export interface TtsPlayerHandle {
  displayText: string | null;
  amplitude: number;
}

export function useTtsPlayer(): TtsPlayerHandle {
  const playerRef = useRef<TtsPlayer | null>(null);
  const phonemeSync = usePhonemeSync();
  const amplitude = 0; // TODO: TTS AnalyserNode amplitude 연결

  useEffect(() => {
    const handler = async (e: Event) => {
      const { audioB64, phonemes } = (e as CustomEvent<{
        audioB64: string;
        phonemes: Phoneme[];
      }>).detail;

      if (!playerRef.current) {
        playerRef.current = new TtsPlayer();
      }

      try {
        const { audioContext } = await playerRef.current.play(
          audioB64,
          () => {
            // 재생 완료 → Python에 알림
            phonemeSync.stop();
            getApi()
              ?.notify_speak_done()
              .catch((err) =>
                console.error("[TtsPlayer] notify_speak_done failed:", err)
              );
          }
        );

        // AudioContext.currentTime 기준으로 음소 싱크 시작
        phonemeSync.start(phonemes, audioContext);
      } catch (err) {
        console.error("[TtsPlayer] play failed:", err);
      }
    };

    window.addEventListener("tts-audio-ready", handler);
    return () => window.removeEventListener("tts-audio-ready", handler);
  }, [phonemeSync]);

  return {
    displayText: phonemeSync.displayText,
    amplitude,
  };
}
