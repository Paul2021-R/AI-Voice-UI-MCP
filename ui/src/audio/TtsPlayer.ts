/**
 * TTS 오디오 재생 매니저
 *
 * Python → push_audio_and_phonemes(audio_b64, phonemes)
 *   → TtsPlayer.play() → AudioBuffer 재생
 *   → 재생 완료 → notify_speak_done() → Python on_speak_done()
 */


export interface PlayResult {
  audioContext: AudioContext;
  startTime: number;
}

export class TtsPlayer {
  private _ctx: AudioContext | null = null;
  private _source: AudioBufferSourceNode | null = null;

  async play(
    audioB64: string,
    onEnded: () => void
  ): Promise<PlayResult> {
    // 기존 재생 중단
    this.stop();

    this._ctx = new AudioContext();

    // WKWebView autoplay 정책 우회 — 사용자 인터랙션 없이도 재생되도록 resume()
    if (this._ctx.state === "suspended") {
      await this._ctx.resume();
    }

    // base64 → ArrayBuffer
    const binary = atob(audioB64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const audioBuffer = await this._ctx.decodeAudioData(bytes.buffer.slice(0));

    this._source = this._ctx.createBufferSource();
    this._source.buffer = audioBuffer;
    this._source.connect(this._ctx.destination);

    const startTime = this._ctx.currentTime;
    this._source.start();
    console.log(`[TtsPlayer] 재생 시작: ${audioBuffer.duration.toFixed(2)}s`);

    this._source.onended = () => {
      onEnded();
    };

    return { audioContext: this._ctx, startTime };
  }

  stop(): void {
    try {
      this._source?.stop();
    } catch {
      // already stopped
    }
    this._source = null;
    this._ctx?.close();
    this._ctx = null;
  }
}
