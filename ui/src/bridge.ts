/**
 * pywebview 브릿지 타입 정의 및 Mock 구현
 *
 * macOS (pywebview): window.pywebview.api 가 자동으로 주입됨
 * 개발/Linux: MockBridge 가 window.pywebview.api 를 대체함
 */

// ------------------------------------------------------------------ //
// JS → Python (JS가 Python 메서드를 호출)
// ------------------------------------------------------------------ //
export interface PyWebViewAPI {
  /** 현재 앱 상태를 반환한다. */
  get_state(): Promise<string>;

  /** 마이크에서 캡처한 오디오 청크(base64)를 Python으로 전달한다. */
  send_audio_chunk(b64Data: string): Promise<void>;

  /** 녹음 완료 후 16kHz WAV(base64)를 Python으로 전달하고 STT를 트리거한다. */
  end_audio(wavB64: string): Promise<void>;

  /** TTS 재생 완료를 Python에 알린다 → on_speak_done() 트리거. */
  notify_speak_done(): Promise<void>;

  /** 대기 중인 TTS 오디오와 음소 데이터를 Python에서 가져온다. */
  get_pending_audio(): Promise<{ audio: string; phonemes: unknown[] }>;
}

// ------------------------------------------------------------------ //
// Python → JS (Python이 JS 콜백을 호출)
// window.evaluate_js("window.__bridge.onStateChange('LISTENING')") 형태로 수신
// ------------------------------------------------------------------ //
export interface PythonPushBridge {
  onStateChange(state: AppState): void;
  /** Python이 오디오 준비 완료를 알린다. 데이터는 get_pending_audio()로 직접 가져간다. */
  onAudioReady(): void;
  /** Python 마이크 캡처 중 진폭 데이터를 수신한다 (0~1). */
  onAmplitude(amplitude: number): void;
}

export type AppState =
  | "IDLE"
  | "LISTENING"
  | "PROCESSING"
  | "SPEAKING"
  | "WAITING";

// ------------------------------------------------------------------ //
// Mock — 개발/Linux 환경용
// ------------------------------------------------------------------ //
class MockBridge implements PyWebViewAPI {
  private _state: AppState = "IDLE";

  async get_state(): Promise<string> {
    console.log("[MockBridge] get_state() →", this._state);
    return this._state;
  }

  async send_audio_chunk(b64Data: string): Promise<void> {
    console.log(`[MockBridge] send_audio_chunk(${b64Data.length} bytes)`);
  }

  async end_audio(wavB64: string): Promise<void> {
    console.log(`[MockBridge] end_audio(wav: ${wavB64.length} chars)`);
  }

  async notify_speak_done(): Promise<void> {
    console.log("[MockBridge] notify_speak_done()");
  }

  async get_pending_audio(): Promise<{ audio: string; phonemes: unknown[] }> {
    console.log("[MockBridge] get_pending_audio()");
    return { audio: "", phonemes: [] };
  }

  /** 테스트용 — 상태를 강제 변경하고 onStateChange 콜백을 발행한다. */
  simulateStateChange(state: AppState): void {
    this._state = state;
    window.__bridge?.onStateChange(state);
  }
}

// ------------------------------------------------------------------ //
// 브릿지 초기화 — 앱 시작 시 1회 호출
// ------------------------------------------------------------------ //
export function initBridge(): void {
  const isPyWebView = !!(window as any).pywebview;

  if (!isPyWebView) {
    const mock = new MockBridge();
    (window as any).pywebview = { api: mock };
    (window as any).__mockBridge = mock;
    console.log("[Bridge] MockBridge 활성화");
  } else {
    console.log("[Bridge] pywebview.api 연결됨");
  }

  // Python push 수신용 콜백 등록
  window.__bridge = {
    onStateChange: (state: AppState) => {
      console.log("[Bridge] 상태 수신:", state);
      window.dispatchEvent(new CustomEvent("app-state-change", { detail: state }));
    },
    onAudioReady: () => {
      console.log("[Bridge] TTS 준비 신호 수신 — get_pending_audio() 호출");
      getApi()?.get_pending_audio().then(({ audio, phonemes }) => {
        if (!audio) return;
        window.dispatchEvent(
          new CustomEvent("tts-audio-ready", { detail: { audioB64: audio, phonemes } })
        );
      });
    },
    onAmplitude: (amplitude: number) => {
      window.dispatchEvent(new CustomEvent("mic-amplitude", { detail: amplitude }));
    },
  };
}

// ------------------------------------------------------------------ //
// 편의 접근자
// ------------------------------------------------------------------ //
export function getApi(): PyWebViewAPI {
  return (window as any).pywebview?.api as PyWebViewAPI;
}

// TypeScript 전역 타입 확장
declare global {
  interface Window {
    __bridge: PythonPushBridge;
    __mockBridge?: MockBridge;
  }
}
