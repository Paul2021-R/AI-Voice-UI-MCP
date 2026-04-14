/**
 * Web Audio API currentTime 기반 음소→단어 동기화 훅.
 *
 * Supertone include_phonemes=true 응답 구조:
 * { phonemes: [{ text: string, start_time: number, end_time: number }] }
 *
 * 음소를 단어 단위로 그루핑하고, rAF 루프에서 currentTime 비교로
 * 현재 표시할 단어를 결정한다. setTimeout 사용 금지 (ADR-001).
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface Phoneme {
  text: string;
  start_time: number;
  end_time: number;
}

export interface Word {
  text: string;
  start_time: number;
  end_time: number;
}

/** 음소 배열을 공백 기준으로 단어 단위로 그루핑한다. */
export function groupPhememesToWords(phonemes: Phoneme[]): Word[] {
  const words: Word[] = [];
  let current: Phoneme[] = [];

  for (const p of phonemes) {
    if (p.text === " " || p.text === "") {
      if (current.length > 0) {
        words.push({
          text: current.map((c) => c.text).join(""),
          start_time: current[0].start_time,
          end_time: current[current.length - 1].end_time,
        });
        current = [];
      }
    } else {
      current.push(p);
    }
  }
  if (current.length > 0) {
    words.push({
      text: current.map((c) => c.text).join(""),
      start_time: current[0].start_time,
      end_time: current[current.length - 1].end_time,
    });
  }
  return words;
}

export interface PhonemeSync {
  /** 현재 표시할 텍스트 (없으면 null) */
  displayText: string | null;
  /** 재생 시작 — audioContext.currentTime 을 기준 시계로 사용 */
  start(phonemes: Phoneme[], audioContext: AudioContext): void;
  /** 정지 및 초기화 */
  stop(): void;
}

export function usePhonemeSync(): PhonemeSync {
  const [displayText, setDisplayText] = useState<string | null>(null);
  const rafRef = useRef<number>(0);
  const wordsRef = useRef<Word[]>([]);
  const startTimeRef = useRef<number>(0);
  const ctxRef = useRef<AudioContext | null>(null);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    setDisplayText(null);
    wordsRef.current = [];
    ctxRef.current = null;
  }, []);

  const start = useCallback(
    (phonemes: Phoneme[], audioContext: AudioContext) => {
      stop();
      wordsRef.current = groupPhememesToWords(phonemes);
      ctxRef.current = audioContext;
      startTimeRef.current = audioContext.currentTime;

      const tick = () => {
        if (!ctxRef.current) return;
        const elapsed =
          ctxRef.current.currentTime - startTimeRef.current;

        const active = wordsRef.current.find(
          (w) => elapsed >= w.start_time && elapsed < w.end_time
        );
        setDisplayText(active?.text ?? null);

        const lastWord = wordsRef.current[wordsRef.current.length - 1];
        if (lastWord && elapsed > lastWord.end_time) {
          // 전체 재생 완료 — 0.3s 후 텍스트 클리어
          setTimeout(() => setDisplayText(null), 300);
          return;
        }
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    },
    [stop]
  );

  useEffect(() => () => stop(), [stop]);

  return { displayText, start, stop };
}
