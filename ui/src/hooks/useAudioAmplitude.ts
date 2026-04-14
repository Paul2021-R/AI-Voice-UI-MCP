/**
 * Web Audio API AnalyserNode 기반 실시간 amplitude 추출 훅.
 * LISTENING: 마이크 입력 레벨
 * SPEAKING:  TTS 출력 레벨
 */

import { useEffect, useRef, useState } from "react";

export interface AudioAmplitudeHandle {
  /** 0~1 사이 정규화된 현재 amplitude */
  amplitude: number;
  /** 마이크 캡처를 시작한다 */
  startMic(): Promise<void>;
  /** 오디오 엘리먼트를 소스로 연결한다 */
  connectAudioElement(el: HTMLAudioElement): void;
  /** 캡처를 중단한다 */
  stop(): void;
  /** Web Audio API AudioContext (음소 싱크 기준 시계용) */
  audioContext: AudioContext | null;
}

export function useAudioAmplitude(): AudioAmplitudeHandle {
  const [amplitude, setAmplitude] = useState(0);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<AudioNode | null>(null);
  const rafRef = useRef<number>(0);
  const dataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);

  const getOrCreateContext = (): AudioContext => {
    if (!ctxRef.current) {
      ctxRef.current = new AudioContext();
    }
    return ctxRef.current;
  };

  const startLoop = (analyser: AnalyserNode) => {
    analyserRef.current = analyser;
    const bufferLength = analyser.frequencyBinCount;
    dataRef.current = new Uint8Array(bufferLength) as Uint8Array<ArrayBuffer>;

    const tick = () => {
      analyser.getByteFrequencyData(dataRef.current!);
      const avg =
        dataRef.current!.reduce((s, v) => s + v, 0) /
        dataRef.current!.length /
        255;
      setAmplitude(avg);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  };

  const startMic = async () => {
    const ctx = getOrCreateContext();
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    sourceRef.current = source;
    startLoop(analyser);
  };

  const connectAudioElement = (el: HTMLAudioElement) => {
    const ctx = getOrCreateContext();
    const source = ctx.createMediaElementSource(el);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyser.connect(ctx.destination);
    sourceRef.current = source;
    startLoop(analyser);
  };

  const stop = () => {
    cancelAnimationFrame(rafRef.current);
    setAmplitude(0);
  };

  useEffect(() => () => stop(), []);

  return {
    amplitude,
    startMic,
    connectAudioElement,
    stop,
    audioContext: ctxRef.current,
  };
}
