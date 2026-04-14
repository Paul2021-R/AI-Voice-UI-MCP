/**
 * Python에서 Push된 앱 상태를 구독하는 React 훅
 */

import { useEffect, useState } from "react";
import { type AppState, getApi } from "./bridge";
import { usePhonemeSync } from "./hooks/usePhonemeSync";

export function useAppState(): AppState {
  const [state, setState] = useState<AppState>("IDLE");

  useEffect(() => {
    // 최초 마운트 시 현재 상태를 가져온다
    getApi()
      ?.get_state()
      .then((s) => setState(s as AppState));

    // Python push 이벤트 구독
    const handler = (e: Event) => {
      setState((e as CustomEvent<AppState>).detail);
    };
    window.addEventListener("app-state-change", handler);
    return () => window.removeEventListener("app-state-change", handler);
  }, []);

  return state;
}

/** 음소 싱크 컨텍스트 — TODO-007에서 실제 Supertone 데이터와 연결된다. */
export function usePhonemeContext() {
  const sync = usePhonemeSync();
  // Python에서 phoneme-sync 이벤트를 수신하면 start() 호출
  useEffect(() => {
    const handler = (e: Event) => {
      const { phonemes, audioContext } = (e as CustomEvent).detail;
      sync.start(phonemes, audioContext);
    };
    window.addEventListener("phoneme-sync-start", handler);
    return () => window.removeEventListener("phoneme-sync-start", handler);
  }, [sync]);

  return sync;
}
