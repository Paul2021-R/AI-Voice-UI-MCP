/**
 * AudioWorklet 기반 마이크 캡처 매니저
 *
 * 사용 흐름:
 *   await mic.start()          — 마이크 열기, PCM 수집 시작
 *   const b64 = await mic.stop() — 수집 종료, 16kHz WAV base64 반환
 *   mic.amplitude              — 현재 RMS amplitude (0~1)
 */

import { arrayBufferToBase64, encodeWav, resampleTo16kHz } from "./wav";

export class MicCapture {
  private _ctx: AudioContext | null = null;
  private _stream: MediaStream | null = null;
  private _worklet: AudioWorkletNode | null = null;
  private _chunks: Float32Array[] = [];
  private _nativeRate = 0;
  private _amplitude = 0;
  private _running = false;

  get amplitude(): number {
    return this._amplitude;
  }

  get isRunning(): boolean {
    return this._running;
  }

  async start(): Promise<void> {
    if (this._running) return;
    this._chunks = [];
    this._amplitude = 0;

    this._stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
      video: false,
    });

    this._ctx = new AudioContext();
    this._nativeRate = this._ctx.sampleRate;

    await this._ctx.audioWorklet.addModule("/mic-processor.js");

    const source = this._ctx.createMediaStreamSource(this._stream);
    this._worklet = new AudioWorkletNode(this._ctx, "mic-processor");

    this._worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
      const chunk = new Float32Array(e.data);
      this._chunks.push(chunk);
      // RMS amplitude 업데이트
      const rms = Math.sqrt(
        chunk.reduce((s, v) => s + v * v, 0) / chunk.length
      );
      this._amplitude = Math.min(1, rms * 6);
    };

    source.connect(this._worklet);
    // destination에 연결하지 않음 — 자기 목소리 피드백 방지
    this._running = true;
  }

  async stop(): Promise<string> {
    if (!this._running) return "";
    this._running = false;
    this._amplitude = 0;

    this._worklet?.disconnect();
    this._stream?.getTracks().forEach((t) => t.stop());
    await this._ctx?.close();

    // 청크 병합
    const totalLength = this._chunks.reduce((s, c) => s + c.length, 0);
    if (totalLength === 0) return "";

    const raw = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this._chunks) {
      raw.set(chunk, offset);
      offset += chunk.length;
    }

    // 16kHz 리샘플링 → WAV 인코딩 → base64
    const resampled = await resampleTo16kHz(raw, this._nativeRate);
    const wavBuffer = encodeWav(resampled, 16000);
    return arrayBufferToBase64(wavBuffer);
  }
}
